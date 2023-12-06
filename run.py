import importlib.util

import inquirer
from src.core.settings import applications_mapping

questions = [
    inquirer.List(
        name="app",
        message="Выберите приложение",
        choices=applications_mapping.keys(),
    )
]

answers = inquirer.prompt(questions=questions)

selected_application = answers.get("app", None)


app_module = importlib.import_module(
    f"src.{applications_mapping[selected_application]}.service"
)
app_module.main()
