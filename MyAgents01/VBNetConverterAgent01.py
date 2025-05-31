vb_converter = Agent(
    role="VB.NET to C# Converter",
    goal="Identify VB.NET projects, create a new Git branch, convert code to C#, and ensure builds succeed",
    tools=[CodeExecutionTool(), GitTool()],
    verbose=True,
    backstory="Specializes in modernizing VB.NET applications to C# while maintaining functionality."
)