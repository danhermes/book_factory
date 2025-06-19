-- LaTeX-specific filter to fix overfull hbox issues
local previous_elements = {}

-- Remove horizontal rules that cause LaTeX issues
function HorizontalRule(elem)
  return {}
end

-- Remove duplicate adjacent headers
function Header(elem)
  local current_text = pandoc.utils.stringify(elem.content)
  
  for i = #previous_elements, math.max(1, #previous_elements - 2), -1 do
    local prev = previous_elements[i]
    if prev and prev.t == "Header" then
      local prev_text = pandoc.utils.stringify(prev.content)
      if current_text == prev_text then
        return {}
      end
      break
    end
  end
  
  table.insert(previous_elements, elem)
  return elem
end

-- Fix code blocks for LaTeX - this is the key fix for your overfull hbox errors
function CodeBlock(elem)
  if FORMAT:match 'latex' then
    -- Split very long lines in code blocks
    local lines = {}
    for line in elem.text:gmatch("[^\r\n]+") do
      if string.len(line) > 80 then
        -- Break long lines at word boundaries
        local words = {}
        for word in line:gmatch("%S+") do
          table.insert(words, word)
        end
        
        local current_line = ""
        for _, word in ipairs(words) do
          if string.len(current_line) + string.len(word) + 1 > 80 then
            if current_line ~= "" then
              table.insert(lines, current_line)
              current_line = word
            else
              -- Word itself is too long, break it
              table.insert(lines, word)
            end
          else
            if current_line == "" then
              current_line = word
            else
              current_line = current_line .. " " .. word
            end
          end
        end
        if current_line ~= "" then
          table.insert(lines, current_line)
        end
      else
        table.insert(lines, line)
      end
    end
    
    elem.text = table.concat(lines, "\n")
    
    -- Add LaTeX attributes for better formatting
    elem.attr.classes = {"breakable"}
    elem.attr.attributes["breaklines"] = "true"
    elem.attr.attributes["postbreak"] = "\\mbox{\\textcolor{red}{$\\hookrightarrow$}\\space}"
  end
  
  return elem
end

-- Handle inline code that might be too long
function Code(elem)
  if FORMAT:match 'latex' and string.len(elem.text) > 60 then
    -- Convert long inline code to a code block
    return pandoc.CodeBlock(elem.text)
  end
  return elem
end

-- Add line breaking hints to long paragraphs
function Para(elem)
  if FORMAT:match 'latex' then
    -- Check for very long strings without spaces
    local modified = false
    local new_content = {}
    
    for _, inline in ipairs(elem.content) do
      if inline.t == "Str" and string.len(inline.text) > 50 then
        -- Insert zero-width spaces to allow line breaking
        local text = inline.text
        text = string.gsub(text, "([%.%,%;%:])", "%1\\allowbreak ")
        text = string.gsub(text, "([%w])([%w][%w][%w][%w][%w])", "%1\\allowbreak %2")
        inline.text = text
        modified = true
      end
      table.insert(new_content, inline)
    end
    
    if modified then
      elem.content = new_content
    end
  end
  
  return elem
end