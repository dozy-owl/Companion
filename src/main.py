from dataclasses import field
from typing import Callable
import flet as ft


@ft.control
class Task(ft.Container):
    task_name: str = ""
    deadline: str = ""
    steps: list[str] = field(default_factory=list)
    on_status_change: Callable[[], None] = field(default=lambda: None)
    on_delete: Callable[["Task"], None] = field(default=lambda task: None)
    on_view: Callable[["Task"], None] = field(default=lambda task: None)
    on_edit: Callable[[ft.Event, "Task"], None] = field(default=lambda e, task: None)
    on_start: Callable[["Task"], None] = field(default=lambda task: None)

    def init(self):
        self.completed = False
        
        self.padding = 15
        self.border_radius = 10
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.margin = ft.Margin(bottom=5)
        
        self.on_click = self.card_clicked

        self.display_task = ft.Checkbox(
            value=False, 
            label=self.task_name, 
            on_change=self.status_changed
        )

        self.deadline_text = ft.Text(
            f"⏰ Дедлайн: {self.deadline}", 
            size=12, 
            color=ft.Colors.ORANGE_700,
            visible=bool(self.deadline)
        )

        self.content = ft.Column(
            spacing=5,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self.display_task,
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.IconButton(
                                    ft.Icons.PLAY_CIRCLE_FILL,
                                    icon_color=ft.Colors.GREEN_400,
                                    tooltip="Запустить сессию",
                                    on_click=self.start_clicked,
                                ),
                                ft.IconButton(
                                    ft.Icons.EDIT,
                                    icon_color=ft.Colors.BLUE_400,
                                    tooltip="Редактировать",
                                    on_click=self.edit_clicked,
                                ),
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    tooltip="Удалить",
                                    on_click=self.delete_clicked,
                                ),
                            ]
                        )
                    ],
                ),
                self.deadline_text,
            ]
        )

    def card_clicked(self, e):
        self.on_view(self)

    def start_clicked(self, e):
        self.on_start(self)

    def edit_clicked(self, e):
        self.on_edit(e, self)

    def status_changed(self, e):
        self.completed = self.display_task.value
        self.on_status_change()

    def delete_clicked(self, e):
        self.on_delete(self)


@ft.control
class CompanionApp(ft.Column):
    def init(self):
        self.expand = True 
        
        self.tasks_list = ft.ListView(expand=True, spacing=10, padding=10)

        self.filter = ft.TabBar(
            scrollable=False,
            tabs=[
                ft.Tab(label="Все"),
                ft.Tab(label="Активные"),
                ft.Tab(label="Завершённые"),
            ],
        )

        self.filter_tabs = ft.Tabs(
            length=3,
            selected_index=0,
            on_change=lambda e: self.update(),
            content=self.filter,
        )

        self.session_view = ft.Container(expand=True, visible=False)

        self.width = 600
        
        self.controls = [
            self.filter_tabs,
            self.tasks_list,
            self.session_view,
        ]

    # --- ЭКРАН СЕССИИ ---
    def start_session(self, task: Task):
        self.filter_tabs.visible = False
        self.tasks_list.visible = False
        self.session_view.visible = True

        if not task.steps:
            self.session_view.content = ft.Column(
                controls=[
                    ft.Text(f"Задача: {task.task_name}", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("В этой задаче нет микрошагов. Просто начните делать!", size=18),
                    ft.FilledButton("Завершить сессию", on_click=lambda e: self.end_session())
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            )
            self.update()
            return

        current_step_index = 0

        task_title = ft.Text(task.task_name, size=20, color=ft.Colors.GREY_600)
        progress_text = ft.Text(f"Шаг 1 из {len(task.steps)}", size=14, color=ft.Colors.GREY_500)
        step_text = ft.Text(task.steps[current_step_index], size=32, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        
        def next_step(e):
            nonlocal current_step_index
            current_step_index += 1
            
            if current_step_index < len(task.steps):
                progress_text.value = f"Шаг {current_step_index + 1} из {len(task.steps)}"
                step_text.value = task.steps[current_step_index]
                self.update()
            else:
                self.end_session(success=True)

        def exit_session(e):
            self.end_session()

        next_btn = ft.FilledButton(
            "Готово, дальше", 
            icon=ft.Icons.CHECK, 
            on_click=next_step, 
            style=ft.ButtonStyle(padding=20, text_style=ft.TextStyle(size=18))
        )
        exit_btn = ft.TextButton("Прервать сессию", on_click=exit_session)

        self.session_view.content = ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=30,
            controls=[
                task_title,
                ft.Divider(),
                progress_text,
                ft.Container(
                    content=step_text,
                    alignment=ft.Alignment.CENTER,
                    padding=20,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    border_radius=15,
                ),
                next_btn,
                exit_btn
            ]
        )
        self.update()

    def end_session(self, success=False):
        self.session_view.visible = False
        self.session_view.content = None
        self.filter_tabs.visible = True
        self.tasks_list.visible = True
        
        if success:
            self.page.show_dialog(ft.SnackBar(ft.Text("Сессия успешно завершена! Отличная работа.")))
            
        self.update()

    # --- ОКНО ПРОСМОТРА ЗАДАЧИ ---
    def show_task_details(self, task: Task):
        steps_controls = []
        if task.steps:
            for i, step in enumerate(task.steps, 1):
                steps_controls.append(
                    ft.Row([
                        ft.Text(f"{i}.", weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                        ft.Text(step, expand=True)
                    ])
                )
        else:
            steps_controls.append(ft.Text("Шагов пока нет.", italic=True, color=ft.Colors.GREY_500))

        def close_dialog(e):
            e.page.pop_dialog()

        def go_to_edit(e):
            e.page.pop_dialog()
            self.open_task_dialog(e, task=task)
            
        def start_from_details(e):
            e.page.pop_dialog()
            self.start_session(task)

        dialog = ft.AlertDialog(
            title=ft.Text(task.task_name, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"⏰ Дедлайн: {task.deadline}", 
                            visible=bool(task.deadline), 
                            color=ft.Colors.ORANGE_700
                        ),
                        ft.Divider(),
                        ft.Text("Микрошаги:", weight=ft.FontWeight.BOLD),
                        ft.Column(
                            controls=steps_controls,
                            spacing=10,
                            scroll=ft.ScrollMode.AUTO
                        ) if task.steps else steps_controls[0],
                    ],
                    tight=True,
                    spacing=15,
                )
            ),
            actions=[
                ft.TextButton("Редактировать", icon=ft.Icons.EDIT, on_click=go_to_edit),
                ft.FilledButton("Начать", icon=ft.Icons.PLAY_ARROW, on_click=start_from_details),
                ft.TextButton("Закрыть", on_click=close_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.page.show_dialog(dialog)

    # --- ОКНО СОЗДАНИЯ / РЕДАКТИРОВАНИЯ ---
    def open_task_dialog(self, e, task: Task = None):
        is_edit = task is not None
        
        task_field = ft.TextField(
            label="Название задачи", 
            autofocus=True,
            value=task.task_name if is_edit else ""
        )
        deadline_field = ft.TextField(
            label="Дедлайн (например: сегодня 18:00)",
            value=task.deadline if is_edit else ""
        )
        
        steps_list = ft.ListView(spacing=10, height=200)

        def add_step_field(e=None, initial_value=""):
            new_step_field = ft.TextField(
                label=f"Микрошаг {len(steps_list.controls) + 1}",
                value=initial_value
            )
            steps_list.controls.append(new_step_field)
            
            if e is not None:
                steps_list.update()  
                new_step_field.focus()

        if is_edit and task.steps:
            for step in task.steps:
                add_step_field(initial_value=step)
        else:
            add_step_field()

        def close_dialog(e):
            e.page.pop_dialog()

        def save_task(e):
            if not task_field.value.strip():
                task_field.error_text = "Введите название"
                task_field.update()
                return

            collected_steps = [
                f.value.strip() 
                for f in steps_list.controls 
                if f.value.strip()
            ]

            if is_edit:
                task.task_name = task_field.value
                task.deadline = deadline_field.value
                task.steps = collected_steps
                
                task.display_task.label = task.task_name
                task.deadline_text.value = f"⏰ Дедлайн: {task.deadline}"
                task.deadline_text.visible = bool(task.deadline)
                task.update()
            else:
                new_task = Task(
                    task_name=task_field.value,
                    deadline=deadline_field.value,
                    steps=collected_steps,
                    on_status_change=self.task_status_change,
                    on_delete=self.task_delete,
                    on_view=self.show_task_details,
                    on_edit=self.open_task_dialog,
                    on_start=self.start_session
                )
                self.tasks_list.controls.append(new_task)
            
            e.page.pop_dialog()
            self.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Редактировать задачу" if is_edit else "Новая задача"),
            content=ft.Container(
                width=400, 
                content=ft.Column(
                    controls=[
                        task_field,
                        deadline_field,
                        ft.Divider(),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Разбивка на шаги:", weight=ft.FontWeight.BOLD),
                                ft.TextButton(
                                    "Добавить шаг", 
                                    icon=ft.Icons.ADD, 
                                    on_click=add_step_field
                                ),
                            ]
                        ),
                        steps_list,
                    ],
                    tight=True,
                    spacing=15,
                )
            ),
            actions=[
                ft.TextButton("Отмена", on_click=close_dialog),
                ft.FilledButton("Сохранить", on_click=save_task),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        e.page.show_dialog(dialog)

    def task_status_change(self):
        self.update()

    def task_delete(self, task):
        self.tasks_list.controls.remove(task)
        self.update()

    def before_update(self):
        status = self.filter.tabs[self.filter_tabs.selected_index].label
        for task in self.tasks_list.controls:
            task.visible = (
                status == "Все"
                or (status == "Активные" and not task.completed)
                or (status == "Завершённые" and task.completed)
            )


def main(page: ft.Page):
    page.title = "Компаньон"
    page.padding = 10
    
    app = CompanionApp()
    
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, 
        on_click=lambda e: app.open_task_dialog(e, task=None),
        tooltip="Добавить задачу"
    )
    
    page.add(app)


ft.run(main)