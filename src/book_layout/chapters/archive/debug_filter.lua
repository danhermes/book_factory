-- Debug filter to see what elements are in your document
function Pandoc(doc)
  print("=== DOCUMENT ANALYSIS ===")
  
  local function walk_blocks(blocks, level)
    level = level or 0
    local indent = string.rep("  ", level)
    
    for i, block in ipairs(blocks) do
      if block.t == "Header" then
        print(indent .. "Header (level " .. block.level .. "): " .. pandoc.utils.stringify(block.content))
      elseif block.t == "HorizontalRule" then
        print(indent .. "HorizontalRule found")
      elseif block.t == "CodeBlock" then
        print(indent .. "CodeBlock found (" .. string.len(block.text) .. " chars)")
      elseif block.t == "Para" then
        local text = pandoc.utils.stringify(block.content)
        if string.len(text) > 100 then
          print(indent .. "Para (long): " .. string.sub(text, 1, 50) .. "...")
        else
          print(indent .. "Para: " .. text)
        end
      elseif block.t == "Div" then
        print(indent .. "Div")
        if block.content then
          walk_blocks(block.content, level + 1)
        end
      else
        print(indent .. block.t .. " element found")
      end
    end
  end
  
  walk_blocks(doc.blocks)
  print("========================")
  
  return doc
end