from aqt import mw

def getConfig():
    return mw.addonManager.getConfig(__name__)

def shouldShowCodeLineNums():
    return getConfig()['code']['lineNums']

def getCodeColorScheme():
    return getConfig()['code']['colorScheme']


def shouldShowEditFieldCheckbox():
    return getConfig()['ui']['editFieldCheckbox']

def isAutoMarkdownEnabled():
    return getConfig()['auto']['enabled']

def getManualMarkdownShortcut():
    return getConfig()['manual']['shortcut']

