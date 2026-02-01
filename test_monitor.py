from runtime.tool_router import execute_tool

run_id = "run-1"

# Agent 1: enumerate
print(execute_tool(run_id=run_id, agent_id="agent_explorer", tool_name="list_files", args={"path":"."}, nl_request="list all files"))

# Agent 2: attempt index read (should block)
try:
    print(execute_tool(run_id=run_id, agent_id="agent_executor", tool_name="read_file", args={"index": 1}, nl_request="read file #2"))
except Exception as e:
    print("EXPECTED BLOCK:", e)
