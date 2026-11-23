
from rich.console import Console

from config import config
from screen import capture_screen
from planner import plan
from memory import Memory
import control


console = Console()


class AgentController:
    def __init__(self):
        self.memory = Memory()
        self.running = False

    def execute(self, action, observation):
        def coordinates():
            x = round(
                action.x * observation["width"] /
                observation["image_width"]
            )
            y = round(
                action.y * observation["height"] /
                observation["image_height"]
            )
            return x, y

        if action.action == "move":
            if action.x is None or action.y is None:
                raise ValueError("Missing coordinates")

            control.move_mouse(*coordinates())
            return "Mouse moved"

        if action.action == "click":
            if action.x is None or action.y is None:
                raise ValueError("Missing coordinates")

            control.click(*coordinates(), button=action.button)
            return f"Clicked using {action.button} button"

        if action.action == "type":
            if action.text is None:
                raise ValueError("Missing text")

            control.type_text(action.text)
            return "Text entered"

        if action.action == "press":
            if action.key is None:
                raise ValueError("Missing key")

            control.press_key(action.key)
            return f"Pressed {action.key}"

        if action.action == "scroll":
            if action.amount is None:
                raise ValueError("Missing scroll amount")

            control.scroll(action.amount)
            return f"Scrolled {action.amount}"

        if action.action == "wait":
            control.wait(action.seconds or 1)
            return "Wait completed"

        raise ValueError(f"Unsupported action: {action.action}")

    def run(self, task):
        self.running = True
        task_id = self.memory.add_task(task)
        experiences = self.memory.retrieve(task)

        console.print(f"\n[bold cyan]Objective:[/bold cyan] {task}")
        console.print("[dim]Autonomous execution started.[/dim]")

        try:
            observation = capture_screen()

            control.set_screen_size(
                observation["width"],
                observation["height"]
            )

            console.print(
                f"[dim]Platform: {observation['platform']}[/dim]"
            )

            console.print(
                f"[dim]Initial screenshot: "
                f"{observation['screenshot_path']}[/dim]"
            )

            for step in range(1, config.max_steps + 1):
                if not self.running:
                    break

                console.print(
                    f"\n[bold cyan]Step {step}/{config.max_steps}[/bold cyan]"
                )

                action = plan(
                    task,
                    observation,
                    self.memory.recent_actions(),
                    experiences
                )

                console.print(
                    f"[bold]Reasoning:[/bold] {action.reasoning}"
                )

                if action.action == "done":
                    self.memory.add_action(
                        task_id,
                        action.model_dump(),
                        "Task completion reported after visual observation",
                        observation["screenshot_path"],
                        observation["screenshot_path"],
                        "verified"
                    )

                    self.memory.finish_task(task_id, "completed")

                    console.print(
                        "\n[bold green]Task completed.[/bold green]"
                    )
                    return True

                if action.action == "ask_user":
                    console.print(
                        f"[yellow]{action.reasoning}[/yellow]"
                    )

                    answer = input("You: ").strip()

                    if not answer:
                        self.memory.finish_task(
                            task_id,
                            "cancelled"
                        )
                        return False

                    task += f"\nUser clarification: {answer}"
                    experiences = self.memory.retrieve(task)
                    continue

                before = observation["screenshot_path"]

                try:
                    result = self.execute(action, observation)

                    console.print(
                        f"[green]Executed:[/green] {result}"
                    )

                    control.wait(0.5)

                    updated = capture_screen()

                    control.set_screen_size(
                        updated["width"],
                        updated["height"]
                    )

                    self.memory.add_action(
                        task_id,
                        action.model_dump(),
                        result,
                        before,
                        updated["screenshot_path"],
                        "executed"
                    )

                    observation = updated

                except Exception as error:
                    console.print(
                        f"[red]Action failed:[/red] {error}"
                    )

                    self.memory.add_action(
                        task_id,
                        action.model_dump(),
                        str(error),
                        before,
                        None,
                        "failed"
                    )

                    observation = capture_screen()

                    control.set_screen_size(
                        observation["width"],
                        observation["height"]
                    )

            self.memory.finish_task(
                task_id,
                "incomplete"
            )

            console.print(
                "\n[yellow]Maximum steps reached.[/yellow]"
            )

            return False

        except KeyboardInterrupt:
            self.memory.finish_task(task_id, "interrupted")
            raise

        except Exception:
            self.memory.finish_task(task_id, "error")
            raise

        finally:
            self.running = False
