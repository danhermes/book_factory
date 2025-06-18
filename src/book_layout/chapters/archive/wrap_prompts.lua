-- Lua filter to make code blocks wrap text
function CodeBlock(elem)
  -- Add wrapping attributes to code blocks
  elem.attr.attributes['style'] = 'white-space: pre-wrap; word-wrap: break-word;'
  return elem
end

function Code(elem)
  -- Handle inline code as well
  elem.attr.attributes['style'] = 'white-space: pre-wrap; word-wrap: break-word;'
  return elem
end