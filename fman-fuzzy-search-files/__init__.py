from fman import DirectoryPaneCommand, show_quicksearch, QuicksearchItem, show_status_message, show_alert
from fman.url import as_human_readable, as_url
from os import listdir
from os.path import join, isdir, dirname
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

# List of excluded folders
exclude_dir_list = [
  r"(^|.*\/)(vendor|node_modules|venv)(\/.*|$)",
  r"(^|.*\/)(_tmp|tmp|_emacs_bak|_deploy)(\/.*|$)",
  r"(^|.*\/)\.git/objects(\/.*|$)",
  r"(^|.*\/)(\.svn|\.hg|\.yarn)(\/.*|$)",
]
exclude_dir_list_patterns = [re.compile(regex) for regex in exclude_dir_list]

def should_exclude_dir(file_path):
  return should_exclude_with_patterns(file_path, exclude_dir_list_patterns)

class FuzzySearchFilesInSubFolders(DirectoryPaneCommand):
  """ Search for all files in all sub-folders recursively until FILE_COUNT_LIMIT is reached """
  file_prefix = ""
  FILE_COUNT_LIMIT = 15000;

  def __call__(self):
    self.current_dir = self.pane.get_path()
    result = show_quicksearch(self._suggest_my_subfolders_and_files)
    if result:
      query, file_path = result
      new_path = dirname(file_path)
      thePane = self.pane
      self.pane.set_path(as_url(new_path), lambda: thePane.place_cursor_at(as_url(file_path)))

  def _suggest_my_subfolders_and_files(self, query):
    self.limit_file_count = self.FILE_COUNT_LIMIT
    self.folders_found = 0
    self.files_found = 0
    current_folder = as_human_readable(self.current_dir)
    prepared_query = prepare_query(query)
    lst_search_items = self.load_files_for_dir(prepared_query, current_folder, '')

    # show status message only when limit is reached
    is_full_message = ''
    if self.limit_file_count <= 0:
      is_full_message = f"!!! reached {self.FILE_COUNT_LIMIT} files limit, you should search in a subfolder !!!"

    show_status_message(
      'folders/files found: ' + str(self.folders_found) + '/' + str(self.files_found) + ' ' + is_full_message, 5)

    return lst_search_items

  def load_files_for_dir(self, prepared_query, parse_dir, base_path):
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
        self.folders_found += 1
        file_name = '[' + file_name + ']'

      match = match_path(file_name, prepared_query)

      if match or not prepared_query:
        lst_search_items.append(QuicksearchItem(file_path, file_name, highlight=match))

      if isdir(file_path):
        new_base_path = join(base_path, file_name_clean)
        if self.limit_file_count > 0:
              lst_search_items += self.load_files_for_dir(prepared_query, file_path, new_base_path)

    lst_search_items.sort(key=lambda x: (len(x.highlight),len(x.value)), reverse=False)
    return lst_search_items
