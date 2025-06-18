-- debug.lua - Test if Lua filters are working at all
function Header(el)
  print("FOUND HEADER: " .. pandoc.utils.stringify(el))
  return el
end

function HorizontalRule()
  print("FOUND HORIZONTAL RULE")
  return {}
end
