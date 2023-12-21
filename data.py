class Lab:
    def __init__(self, name, number, semester, module):
        self.name = name
        self.number = number
        self.semester = semester
        self.module = module

    def run(self, option, message, bot):
        return self.module.main(option, message, bot)

# Создание экземпляров класса Lab
labs = {
    "sem2": [Lab("2.23 'Барометрическая формула. Распределение Больцман'", 2.23, "sem2", __import__("lab2_23"))]
}

#options = ["Составление вывода", "Оптимальные параметры установки", "Расчёт значений", "Построение графиков", "Личный созвон"]
options = ["Вывод", "Калибровка установки", "Расчёт", "Графики", "Созвон"]