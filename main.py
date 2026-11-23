
import platform

from rich.console import Console
from rich.panel import Panel

from config import config, PLATFORM, SCREENSHOTS_DIR
from controller import AgentController


console = Console()


def main():
    agent = AgentController()

    console.print(
        Panel(
            "[bold cyan]ABSOLUT[/bold cyan]\n"
            "Autonomous Desktop Intelligence\n\n"
            f"Model: {config.model}\n"
            f"OS: {platform.system()}\n"
            f"Backend: {PLATFORM}\n"
            f"Experiences: {len(agent.memory.data['experiences'])}\n"
            f"Screenshots: {SCREENSHOTS_DIR}\n"
            "Mode: Autonomous",
            title="Desktop Agent",
            border_style="cyan"
        )
    )

    while True:
        try:
            task = console.input(
                "\n[bold cyan]absolut > [/bold cyan]"
            ).strip()

            if not task:
                continue

            if task.lower() in ("exit", "quit"):
                break

            if task.lower() == "clear":
                console.clear()
                continue

            if task.lower() == "memory":
                console.print_json(
                    data=agent.memory.data
                )
                continue

            if task.lower() == "history":
                console.print_json(
                    data=agent.memory.recent_actions(20)
                )
                continue

            if task.lower() == "screenshots":
                files = sorted(
                    SCREENSHOTS_DIR.glob("*.png"),
                    reverse=True
                )

                for file in files[:20]:
                    console.print(str(file))

                continue

            agent.run(task)

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")

        except EOFError:
            break

        except Exception as error:
            console.print(
                f"\n[bold red]Error:[/bold red] {error}"
            )

    console.print("[dim]Absolut stopped.[/dim]")


if __name__ == "__main__":
    main()
