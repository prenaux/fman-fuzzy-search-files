from fman import DirectoryPaneCommand, show_quicksearch, QuicksearchItem, show_status_message, show_alert
from fman.url import as_human_readable, as_url
from os import listdir
from os.path import join, isdir, dirname
from collections import deque
import fnmatch
import re

def replace_spaces(s):
  # Replace spaces that aren't preceded by a backslash with .*
  return re.sub(r'(?<!\\) ', '.*', s)

def prepare_query(query):
  try:
    if query.startswith(":"):
      # glob pattern
      regex = fnmatch.translate(query[1:])
    else:
      # regex
      # regex = query
      regex = replace_spaces(query)
    return re.compile(regex, re.IGNORECASE)
  except:
    return None

def match_path(file_name, prepared_query):
  if prepared_query:
    try:
      match = prepared_query.search(file_name)
      if match:
        start = match.start()
        end = match.end()
        return list(range(start, end))
    except:
      return None
  return None

def should_exclude_with_patterns(file_path, exclude_patterns):
  for pattern in exclude_patterns:
    if pattern.search(file_path):
      return True
  return False

# List of excluded dirs
exclude_dir_list = [
  r"(^|.*\/)(vendor|node_modules|venv)(\/.*|$)",
  r"(^|.*\/)(_tmp|tmp|_emacs_bak|_deploy)(\/.*|$)",
  r"(^|.*\/)\.git/objects(\/.*|$)",
  r"(^|.*\/)(\.svn|\.hg|\.yarn)(\/.*|$)",
]
exclude_dir_list_patterns = [re.compile(regex) for regex in exclude_dir_list]

def should_exclude_dir(file_path):
  return should_exclude_with_patterns(file_path, exclude_dir_list_patterns)

class FuzzySearchFilesInSubDirs(DirectoryPaneCommand):
  """ Search for all files in all sub-dirs recursively until COUNT_LIMIT is reached """
  file_prefix = ""
  COUNT_LIMIT = 15000;

  def __call__(self):
    self.max_depth = 0
    self.current_dir = self.pane.get_path()
    result = show_quicksearch(self._suggest_my_subdirs_and_files)
    if result:
      query, file_path = result
      new_path = dirname(file_path)
      thePane = self.pane
      self.pane.set_path(as_url(new_path), lambda: thePane.place_cursor_at(as_url(file_path)))

  def _suggest_my_subdirs_and_files(self, query):
    self.limit_file_count = self.COUNT_LIMIT
    self.dirs_found = 0
    self.files_found = 0
    current_dir = as_human_readable(self.current_dir)
    prepared_query = prepare_query(query)
    lst_search_items = self.load_files_for_dir_breadth_first(prepared_query, current_dir, '')

    # show status message only when limit is reached
    is_full_message = ''
    if self.limit_file_count <= 0:
      is_full_message = f" !!! reached {self.COUNT_LIMIT} files/dirs limit !!!"

    show_status_message(
      'Found: ' + str(self.files_found) + ' files, ' + str(self.dirs_found) + ' dirs, searched_depth: ' + str(self.max_depth) + ' dirs' + is_full_message, 5)

    return lst_search_items

  def load_files_for_dir_depth_first(self, prepared_query, parse_dir, base_path):
    if should_exclude_dir(base_path):
      return []

    lst_search_items = []
    for file_name in listdir(parse_dir):
      self.limit_file_count -= 1
      self.files_found += 1
      file_path = join(parse_dir, file_name)
      file_name_clean = file_name
      file_name = join(base_path, file_name)

      if isdir(file_path):
        self.dirs_found += 1
        file_name = '[' + file_name + ']'

      match = match_path(file_name, prepared_query)

      if match or not prepared_query:
        lst_search_items.append(QuicksearchItem(file_path, file_name, highlight=match))

      if isdir(file_path):
        new_base_path = join(base_path, file_name_clean)
        if self.limit_file_count > 0:
              lst_search_items += self.load_files_for_dir_depth_first(prepared_query, file_path, new_base_path)

    lst_search_items.sort(key=lambda x: (len(x.highlight),len(x.value)), reverse=False)
    return lst_search_items

  def load_files_for_dir_breadth_first(self, prepared_query, parse_dir, base_path):
    if should_exclude_dir(base_path):
      return []

    lst_search_items = []
    queue = deque([(parse_dir, base_path, 0)])  # Add depth parameter to queue items

    while queue:
      parse_dir, base_path, depth = queue.popleft()  # Unpack depth from queue item
      self.max_depth = max(self.max_depth, depth)

      for file_name in listdir(parse_dir):
        self.limit_file_count -= 1
        if self.limit_file_count < 0:
          break

        self.files_found += 1
        file_path = join(parse_dir, file_name)
        file_name_clean = file_name
        file_name = join(base_path, file_name)

        if isdir(file_path):
          self.dirs_found += 1
          file_name = '[' + file_name + ']'
          new_base_path = join(base_path, file_name_clean)
          queue.append((file_path, new_base_path, depth + 1))  # Increment depth for subdirectories

        match = match_path(file_name, prepared_query)

        if match or not prepared_query:
          lst_search_items.append(QuicksearchItem(file_path, file_name, highlight=match))

      if self.limit_file_count < 0:
        break

    lst_search_items.sort(key=lambda x: (len(x.highlight),len(x.value)), reverse=False)
    return lst_search_items
