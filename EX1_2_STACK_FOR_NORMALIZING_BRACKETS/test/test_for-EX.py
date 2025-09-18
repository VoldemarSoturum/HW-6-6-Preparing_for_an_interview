import unittest
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Импортируем функции и класс, которые будем тестировать.
# !!!ПЕРЕД ЗАПУСКОМ ТЕСТА!!! имя импорта из файла 'EX1' замените на файла без расширения .py,
# где реализованы Stack, is_brackets_balanced и verdict_text. Иначе тест упадёт.
from EX1_2_STACK_FOR_NORMALIZING_BRACKETS import Stack, is_brackets_balanced, verdict_text



# === ТЕСТЫ ДЛЯ КЛАССА STACK ===
class TestStack(unittest.TestCase):
    def test_new_stack_is_empty(self):
        # Проверяем, что новый стек изначально пуст
        st = Stack()
        self.assertTrue(st.is_empty())     # метод is_empty() должен вернуть True
        self.assertEqual(st.size(), 0)     # размер нового стека = 0

    def test_push_pop_lifo(self):
        # Проверяем, что стек работает по принципу LIFO (последний вошёл — первый вышел)
        st = Stack()
        st.push(1)     # кладём 1
        st.push(2)     # кладём 2
        st.push(3)     # кладём 3
        self.assertEqual(st.size(), 3)     # в стеке должно быть 3 элемента
        self.assertEqual(st.pop(), 3)      # первым снимется 3
        self.assertEqual(st.pop(), 2)      # затем 2
        self.assertEqual(st.pop(), 1)      # затем 1
        self.assertTrue(st.is_empty())     # в итоге стек пустой

    def test_peek_does_not_remove(self):
        # Проверяем, что peek возвращает верхний элемент, но не удаляет его
        st = Stack()
        st.push("x")
        self.assertEqual(st.peek(), "x")   # верхний элемент — "x"
        self.assertFalse(st.is_empty())    # стек всё ещё не пуст
        self.assertEqual(st.size(), 1)     # размер не изменился

    def test_pop_empty_raises(self):
        # Проверяем, что pop() из пустого стека вызывает исключение IndexError
        st = Stack()
        with self.assertRaises(IndexError):
            st.pop()

    def test_peek_empty_raises(self):
        # Проверяем, что peek() из пустого стека вызывает исключение IndexError
        st = Stack()
        with self.assertRaises(IndexError):
            st.peek()


# === ТЕСТЫ ДЛЯ ФУНКЦИИ ПРОВЕРКИ СКОБОК ===
class TestBracketsBalanced(unittest.TestCase):
    def test_balanced_examples(self):
        # Проверяем корректные примеры (должны вернуть True)
        samples = [
            "(((([{}]))))",               # вложенные все три типа
            "[([])((([[[]]])))]{()}",     # сложная правильная комбинация
            "{{[()]}}",                   # короткий пример
            "",                           # пустая строка считается сбалансированной
            "()[]{}",                     # разные типы скобок подряд
            "([]){}[()]"                  # разные типы скобок вперемешку
        ]
        for s in samples:
            # subTest позволяет проверять каждый пример отдельно,
            # чтобы при падении видеть, какой именно не прошёл
            with self.subTest(s=s):
                self.assertTrue(
                    is_brackets_balanced(s),
                    msg=f"Ожидали True для {s!r}"
                )

    def test_unbalanced_examples(self):
        # Проверяем некорректные примеры (должны вернуть False)
        samples = [
            "}{}",         # начинается с закрывающей
            "{{[(])]}}",   # неправильный порядок
            "[[{())}]",    # перепутаны скобки
            "(",           # незакрытая
            "(((((",       # много незакрытых
            "())",         # лишняя закрывающая
            "([)]",        # перекрёстное закрытие
            "((]})",       # разные типы скобок перепутаны
        ]
        for s in samples:
            with self.subTest(s=s):
                self.assertFalse(
                    is_brackets_balanced(s),
                    msg=f"Ожидали False для {s!r}"
                )

    def test_ignores_non_bracket_chars(self):
        # Проверка: если в строке есть посторонние символы (буквы, цифры),
        # функция должна их игнорировать, и всё равно корректно анализировать структуру скобок.
        s = "func(a[0] + b{2})"  # правильная структура скобок
        self.assertTrue(is_brackets_balanced(s))

    def test_verdict_text(self):
        # Проверка функции-обёртки verdict_text, которая возвращает строку вместо True/False
        self.assertEqual(verdict_text("()"), "Сбалансированно")
        self.assertEqual(verdict_text("([)]"), "Несбалансированно")
    # Супер-тесты, усиленные для отлова крайних случаев
class TestExtraCases(unittest.TestCase):
    def test_deep_nesting_parentheses(self):
        # Очень глубокая вложенность (без рекурсии в коде — всё ок)
        n = 10000
        s = "(" * n + ")" * n
        self.assertTrue(is_brackets_balanced(s))

    def test_long_mixed_sequence(self):
        # Длинная правильная последовательность
        s = "([]){}" * 5000 + "{{[()]}}" * 3000 + "[()]" * 4000
        self.assertTrue(is_brackets_balanced(s))

    def test_long_incorrect_tail(self):
        # Почти правильная, но с одной ошибкой в конце
        s = "([]){}" * 10000 + "("
        self.assertFalse(is_brackets_balanced(s))

    def test_exceptions_messages(self):
        st = Stack()
        with self.assertRaisesRegex(IndexError, "pop from empty stack"):
            st.pop()
        with self.assertRaisesRegex(IndexError, "peek from empty stack"):
            st.peek()

    def test_repr_contains_internal_data(self):
        st = Stack()
        st.push(1); st.push(2)
        self.assertIn("Stack([", repr(st))  # просто sanity-check представления

    def test_verdict_localization(self):
        self.assertEqual(verdict_text("()[]{}"), "Сбалансированно")
        self.assertEqual(verdict_text("([)]"), "Несбалансированно")

# Запуск тестов при прямом вызове файла
if __name__ == "__main__":
    unittest.main(verbosity=2)
