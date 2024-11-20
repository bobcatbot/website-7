from plugin_list import plugins

def fetch_plugins(dash):
  plugins_dict = list(plugins.items())
  for _item, _plugin in plugins_dict:
    plug = dash.get(_item)
    _plugin['status'] = plug['status']
  return plugins_dict