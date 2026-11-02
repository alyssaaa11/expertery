#!/bin/zsh
clear; echo "Watching Muse Code round 1c (Forge factory). Close this window anytime; it does not stop Muse."; echo
tail -n +1 -f ~/projects/forge/results/muse-final-r1c.jsonl | jq -r --unbuffered '
 if .payload_type=="todo.snapshot.updated" then "\n📋 PLAN: " + ([.payload.facts.items[] | (if .status=="completed" then "✅ " elif .status=="in_progress" then "⏳ " else "▫️ " end) + .text] | join("  ")) + "\n"
 elif .payload_type=="tool.result" then
   (.payload.correlation_facts.tool_name) as $n | (.payload.text) as $t |
   if $n=="read_file" then "📖 read   " + (($t|split("`"))[1] // "")
   elif $n=="bash" then ( ($t|fromjson? // {}) as $d | "⚙️  ran    " + (($d.command // "")|split("\n")[0]|.[0:110]) + "  → exit " + (($d.exit_code // "?")|tostring))
   elif $n=="edit_file" then "✏️  edited " + (($t|split("\n"))[1] // "") + "  " + ([($t|split("\n"))[] | select(startswith("+") and (startswith("+++")|not))][0] // "" | .[0:90])
   elif $n=="write_file" then "📝 " + ($t|split(" (")[0]|sub("~/projects/forge/";""))
   elif $n=="write_todos" then empty
   else "🔎 " + $n end
 elif .payload_type=="run.terminal.completed" then "\n🏁 DONE. Muse report:\n\n" + .payload.text
 else empty end'
