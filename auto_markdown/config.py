from aqt import mw

def getConfig():
    return mw.addonManager.getConfig(__name__)

def shouldShowCodeLineNums():
    return getConfig()['code']['lineNums']

def getCodeColorScheme():
    return getConfig()['code']['colorScheme']

def isAutoMarkdownEnabled():
    return getConfig()['auto']['enabled']

def shouldShowEditFieldCheckbox():
    return getConfig()['auto']['uiEditFieldCheckbox']

def getManualMarkdownShortcut():
    return getConfig()['manual']['shortcut']

def shouldShowFieldMarkdownButton():
    return getConfig()['manual']['uiToggleFieldMarkdownButton']