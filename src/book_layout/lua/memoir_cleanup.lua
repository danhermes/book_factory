-- Combined Lua filter for memoir cleanup
local last_header = nil

-- Remove horizontal rules (dividing lines)
function HorizontalRule(elem)
  return {}
end

-- Remove duplicate adjacent headers
function Header(elem)
  if last_header and pandoc.utils.stringify(elem.content) == pandoc.utils.stringify(last_header.content) then
    last_header = ""
    return {}  -- Remove duplicate
  end
  
  last_header = elem
  return elem
end

-- Make code blocks wrap text
function CodeBlock(elem)
  elem.attr.attributes['style'] = 'white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;'
  return elem
end

-- Make inline code wrap text
function Code(elem)
  elem.attr.attributes['style'] = 'white-space: pre-wrap; word-wrap: break-word;'
  return elem
end