-- Quote a value for POSIX shells: local shell_quote = dofile(".../shell-quote.lua")
return function(value)
    return "'" .. tostring(value):gsub("'", "'\\''") .. "'"
end
