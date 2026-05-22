# Record a GIF demo of Modal Parallel Search with Charm VHS.
# Install VHS: https://github.com/charmbracelet/vhs
#   brew install vhs
# Then run from the repository root:
#   vhs examples/demo.tape

Output examples/modal-parallel-search-demo.gif
Set Shell "bash"
Set FontSize 18
Set Width 1280
Set Height 760
Set Padding 16
Set Theme "Catppuccin Mocha"

Type "clear"
Enter
Sleep 500ms

Type "# Modal Parallel Search: one agent command, many serverless searches"
Enter
Sleep 1s

Type "modal run skills/modal-parallel-search/scripts/modal_search_cli.py --queries-json '[\"Modal serverless coding agents\", \"Pi coding agent skills\", \"AI agent terminal CLI tools\"]' --max-results 2 --timelimit w"
Enter
Sleep 14s

Type "# Done: multiple web-search angles fanned out across Modal containers"
Enter
Sleep 2s
