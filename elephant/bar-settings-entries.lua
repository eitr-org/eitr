local paths = dofile((os.getenv("EITR_LIBRARY_ROOT") or "/usr/share/eitr/lib") .. "/paths.lua")
local choices = dofile(paths.code("elephant/choice-entries.lua"))
local script = paths.code("quickshell/desktop-bar/scripts/bar-settings.py")

return function(key, options)
    return choices(script, key, options)
end
