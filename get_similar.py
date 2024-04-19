import gensim.downloader as api
import pymorphy3
import numpy as np
from spellchecker import SpellChecker

spell = SpellChecker(language='ru')
morph = pymorphy3.MorphAnalyzer()
model = api.load("word2vec-ruscorpora-300")


def correct_text(text):
    """
    Корректирует текст с помощью проверки орфографии каждого слова во входном тексте.

    Параметры:
        text (str): Входной текст для коррекции.

    Возвращает:
        str: Исправленный текст после проверки орфографии.
    """
    words = text.split()
    corrected_text = []
    for word in words:
        corrected_text.append(spell.correction(word))
    return ' '.join(corrected_text)


def get_part_of_speech(word):
    """
    Получает часть речи слова с помощью pymorphy3 для указанного слова.

    Параметры:
        word (str): Слово, для которого необходимо получить часть речи.

    Возвращает:
        str: Часть речи указанного слова.
    """
    parsed_word = morph.parse(word)[0]
    return parsed_word.tag.POS


def get_base_form(word):
    """
    Получить базовую форму слова, используя морфологическую аналитику.

    Параметры:
        word (str): Слово, для которого нужно получить базовую форму.

    Возвращает:
        str: Базовая форма слова.
    """
    parsed_word = morph.parse(word)[0]
    return parsed_word.normal_form


def word2vec(word):
    """
    Функция, возвращающая вектор слова.

    Параметры:
        word (str): Слово, для которого должен быть получен вектор слов.

    Возвращает:
        float: Вектор для данного слова, если оно существует, в противном случае возвращает 0.
    """
    try:
        return model[word]
    except KeyError:
        return 0


def cosdis(v1, v2):
    """
    Вычислите косинусное расстояние между двумя векторами.

    Параметры
        v1 (float): Первый вектор
        v2 (float): Второй вектор

    Возвращает:
        float: Косинусное сходство между двумя векторами
    """
    dot_product = np.dot(v1, v2)
    norm_vector1 = np.linalg.norm(v1)
    norm_vector2 = np.linalg.norm(v2)
    cosine_sim = dot_product / (norm_vector1 * norm_vector2)
    return cosine_sim


def similar(line_1, line_2):
    """
    Рассчитайте сходство между двумя строками текста на основе векторов слов.

    Параметры:
        line_1 (str): первая строка текста для сравнения.
        line_2 (str): вторая строка текста для сравнения.

    Возврат:
        float: значение с плавающей запятой, представляющее сходство между двумя входными строками.
    """
    line_1 = correct_text(line_1)
    line_2 = correct_text(line_2)
    line_1_sim, line_2_sim = [], []
    for word in line_1.split():
        base_form = get_base_form(word)
        part_of_speech = get_part_of_speech(word)
        if base_form and part_of_speech:
            vector = word2vec(f"{base_form}_{part_of_speech}")
            line_1_sim.append(vector)

    for word in line_2.split():
        base_form = get_base_form(word)
        part_of_speech = get_part_of_speech(word)
        if base_form and part_of_speech:
            vector = word2vec(f"{base_form}_{part_of_speech}")
            line_2_sim.append(vector)

    if not line_1_sim or not line_2_sim:
        return 0.0

    average_line_1 = sum(line_1_sim) / len(line_1_sim)
    average_line_2 = sum(line_2_sim) / len(line_2_sim)

    return cosdis(average_line_1, average_line_2)
print(similar('челолвека', 'люди'))