-- Remove duplicate adjacent headers
-- function Header(elem)
--   local text = pandoc.utils.stringify(elem)
--   --local text = elem.text
--   if ((text ~= "") and (text == last_header)) then
--     print("FOUND DUPLICATE HEADER: " .. text)
--     last_header = ""
--     return {}  -- Remove duplicate
--   end
--   --print("FOUND HEADER: " .. text)
--   last_header = text
--   return elem
-- end

local last_header = ""

function Header(elem)
  local text = pandoc.utils.stringify(elem)
  if ((text ~= "") and (text == last_header)) then
    print("FOUND DUPLICATE HEADER: " .. text)
    last_header = ""
    return pandoc.RawBlock('latex', '') -- Insert an empty raw LaTeX block
  end
  print("FOUND HEADER: " .. text)
  last_header = text
  return elem
end


-- Remove horizontal rules  
function HorizontalRule()
  return pandoc.RawBlock('latex', '')
end


-- wrap_code.lua
function CodeBlock(el)
  if el.text then
    -- Construct LaTeX code for a wrapped listings environment
    print("WRAPPING CODE BLOCK: " .. el.text)
    local wrapped_code = "\\begin{lstlisting}[breaklines=true]\n" .. el.text .. "\n\\end{lstlisting}"
    return pandoc.RawBlock('latex', wrapped_code)
  end
  return el
end




-- -- Make code blocks wrap text
-- function CodeBlock(elem)
--   print("FOUND CODE BLOCK: " .. elem.text)
--   elem.text = pandoc.pipe("fold", {"-w", "60"}, elem.text)
--   print("FOLDED CODE BLOCK: " .. elem.text)
--   --elem.attr.attributes['style'] = 'white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;'
--   return elem
-- end

-- Initialize
last_header = ""