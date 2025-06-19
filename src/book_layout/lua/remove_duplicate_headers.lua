-- Lua filter to remove duplicate adjacent headers
local last_header = nil

function Header(elem)
  -- If this header has the same text as the previous header, skip it
  if last_header and pandoc.utils.stringify(elem.content) == pandoc.utils.stringify(last_header.content) then
    return {}  -- Remove duplicate
  end
  
  last_header = elem
  return elem
end