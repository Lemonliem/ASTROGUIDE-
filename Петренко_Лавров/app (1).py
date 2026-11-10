"""
AstroGuide — сайт на Dash: карта звёздного неба (вид изнутри небесной сферы, как «Сфера» в Daff Moon), нейросеть (заглушка), о проекте.
Запуск:  python app.py   ->  http://127.0.0.1:8050

Структура файла:
  1. Данные          — каталог звёзд, созвездия, планеты (загружаются один раз)
  2. Астрономия      — расчёты на Astropy + numpy (alt/az, планеты, эклиптика)
  3. Карта неба      — слои Plotly и сборка фигуры build_sky_figure()
  4. Интерфейс       — стили, шапка, секции, подвал
  5. Callback'и      — время (слайдер, «Сейчас»), координаты, обновление карты
"""
import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import (
    SkyCoord, BarycentricMeanEcliptic, EarthLocation, get_body,
    solar_system_ephemeris,
)
from astropy.utils import iers

from dash import Dash, html, dcc, Input, Output, State, callback, ctx, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go



# ============================================================================
# 1. ДАННЫЕ
# ============================================================================

# ключ: (название, RA°, Dec°, звёздная величина)  — эпоха J2000
STARS = {
    "sirius":     ("Сириус",            101.287, -16.716, -1.46),
    "canopus":    ("Канопус",            95.988, -52.696, -0.74),
    "arcturus":   ("Арктур",            213.915,  19.182, -0.05),
    "rigil":      ("Ригиль Кентавр",    219.900, -60.834, -0.01),
    "vega":       ("Вега",              279.235,  38.784,  0.03),
    "capella":    ("Капелла",            79.172,  45.998,  0.08),
    "rigel":      ("Ригель",             78.634,  -8.202,  0.13),
    "procyon":    ("Процион",           114.825,   5.225,  0.34),
    "betelgeuse": ("Бетельгейзе",        88.793,   7.407,  0.50),
    "achernar":   ("Ахернар",            24.429, -57.237,  0.46),
    "hadar":      ("Хадар",             210.956, -60.373,  0.61),
    "altair":     ("Альтаир",           297.696,   8.868,  0.76),
    "acrux":      ("Акрукс",            186.650, -63.099,  0.76),
    "aldebaran":  ("Альдебаран",         68.980,  16.509,  0.85),
    "spica":      ("Спика",             201.298, -11.161,  0.97),
    "antares":    ("Антарес",           247.352, -26.432,  1.06),
    "pollux":     ("Поллукс",           116.329,  28.026,  1.14),
    "fomalhaut":  ("Фомальгаут",        344.413, -29.622,  1.16),
    "deneb":      ("Денеб",             310.358,  45.280,  1.25),
    "mimosa":     ("Бекрукс",           191.930, -59.689,  1.25),
    "regulus":    ("Регул",             152.093,  11.967,  1.35),
    "castor":     ("Кастор",            113.650,  31.888,  1.58),
    "gacrux":     ("Гакрукс",           187.791, -57.113,  1.64),
    "bellatrix":  ("Беллатрикс",         81.283,   6.350,  1.64),
    "elnath":     ("Эльнат",             81.573,  28.608,  1.65),
    "alnilam":    ("Альнилам",           84.053,  -1.202,  1.69),
    "alnitak":    ("Альнитак",           85.190,  -1.943,  1.77),
    "shaula":     ("Шаула",             263.402, -37.104,  1.62),
    "dubhe":      ("Дубхе",             165.932,  61.751,  1.79),
    "alioth":     ("Алиот",             193.507,  55.960,  1.77),
    "mirfak":     ("Мирфак",             51.081,  49.861,  1.80),
    "alkaid":     ("Алькаид",           206.885,  49.313,  1.86),
    "polaris":    ("Полярная",           37.955,  89.264,  1.98),
    "mizar":      ("Мицар",             200.981,  54.925,  2.04),
    "saiph":      ("Саиф",               86.939,  -9.670,  2.06),
    "algieba":    ("Альгиеба",          154.993,  19.842,  2.01),
    "denebola":   ("Денебола",          177.265,  14.572,  2.14),
    "sadr":       ("Садр",              305.557,  40.257,  2.20),
    "mintaka":    ("Минтака",            83.002,  -0.299,  2.23),
    "schedar":    ("Шедар",              10.127,  56.537,  2.24),
    "caph":       ("Каф",                 2.295,  59.150,  2.27),
    "merak":      ("Мерак",             165.460,  56.382,  2.37),
    "phecda":     ("Фекда",             178.458,  53.695,  2.44),
    "gienah":     ("Гиенах",            311.553,  33.970,  2.50),
    "gamma_cas":  ("γ Кассиопеи",        14.177,  60.717,  2.47),
    "ruchbah":    ("Рукбах",             21.454,  60.235,  2.68),
    "delta_cru":  ("δ Южного Креста",   183.786, -58.749,  2.80),
    "delta_cyg":  ("δ Лебедя",          296.244,  45.131,  2.87),
    "albireo":    ("Альбирео",          292.680,  27.960,  3.10),
    "megrez":     ("Мегрец",            183.857,  57.033,  3.31),
    "segin":      ("Сегин",              28.599,  63.670,  3.38),
    # ---- дополнительные звёзды для новых созвездий ----
    "kochab":     ("Кохаб",             222.676,  74.156,  2.08),
    "pherkad":    ("Феркад",            230.182,  71.834,  3.05),
    "yildun":     ("Йильдун",           263.054,  86.586,  4.36),
    "eps_umi":    ("ε Малой Медведицы", 251.493,  82.037,  4.20),
    "zeta_umi":   ("ζ Малой Медведицы", 236.015,  77.795,  4.30),
    "eta_umi":    ("η Малой Медведицы", 244.376,  75.755,  4.95),
    "sheliak":    ("Шелиак",            282.520,  33.363,  3.52),
    "sulafat":    ("Сулафат",           284.736,  32.690,  3.24),
    "delta_lyr":  ("δ Лиры",            283.626,  36.899,  4.30),
    "zeta_lyr":   ("ζ Лиры",            281.194,  37.605,  4.36),
    "tarazed":    ("Таразед",           296.565,  10.613,  2.72),
    "alshain":    ("Альшаин",           298.828,   6.407,  3.71),
    "delta_aql":  ("δ Орла",            291.375,   3.115,  3.36),
    "lambda_aql": ("λ Орла",            286.562,  -4.883,  3.44),
    "alhena":     ("Альхена",            99.428,  16.399,  1.93),
    "tejat":      ("Теджат",             95.740,  22.514,  2.88),
    "mebsuta":    ("Мебсута",           100.983,  25.131,  3.06),
    "wasat":      ("Васат",             110.031,  21.982,  3.53),
    "propus":     ("Пропус",             93.719,  22.507,  3.28),
    "zeta_tau":   ("ζ Тельца",           84.411,  21.143,  3.00),
    "eps_tau":    ("ε Тельца",           67.154,  19.180,  3.53),
    "gamma_tau":  ("γ Тельца",           64.948,  15.628,  3.65),
    "delta_tau":  ("δ Тельца",           65.734,  17.543,  3.76),
    "theta_tau":  ("θ Тельца",           67.166,  15.871,  3.40),
    "mirzam":     ("Мирзам",             95.675, -17.956,  1.98),
    "adhara":     ("Адара",             104.656, -28.972,  1.50),
    "wezen":      ("Везен",             107.098, -26.393,  1.84),
    "aludra":     ("Алудра",            111.024, -29.303,  2.45),
    "furud":      ("Фурут",              95.078, -30.063,  3.00),
    "gomeisa":    ("Гомейса",           111.788,   8.289,  2.89),
    "dschubba":   ("Дшубба",            240.083, -22.622,  2.32),
    "graffias":   ("Графиас",           241.359, -19.805,  2.62),
    "pi_sco":     ("π Скорпиона",       239.713, -26.114,  2.89),
    "sigma_sco":  ("σ Скорпиона",       245.297, -25.593,  2.90),
    "tau_sco":    ("τ Скорпиона",       248.971, -28.216,  2.82),
    "eps_sco":    ("ε Скорпиона",       252.541, -34.293,  2.29),
    "mu_sco":     ("μ Скорпиона",       252.968, -38.047,  3.00),
    "zeta_sco":   ("ζ Скорпиона",       253.499, -42.361,  3.62),
    "eta_sco":    ("η Скорпиона",       258.038, -43.239,  3.33),
    "sargas":     ("Саргас",            264.330, -42.998,  1.87),
    "iota_sco":   ("ι Скорпиона",       266.896, -40.127,  3.00),
    "kappa_sco":  ("κ Скорпиона",       265.622, -39.030,  2.41),
    "markab":     ("Маркаб",            346.190,  15.205,  2.49),
    "scheat":     ("Шеат",              345.944,  28.083,  2.42),
    "algenib":    ("Альгениб",            3.309,  15.184,  2.83),
    "alpheratz":  ("Альферац",            2.097,  29.091,  2.06),
    "mirach":     ("Мирах",              17.433,  35.621,  2.06),
    "almach":     ("Аламак",             30.975,  42.330,  2.26),
    "delta_and":  ("δ Андромеды",         9.832,  30.861,  3.27),
    "algol":      ("Алголь",             47.042,  40.956,  2.10),
    "zeta_per":   ("ζ Персея",           58.533,  31.884,  2.85),
    "eps_per":    ("ε Персея",           59.464,  40.010,  2.89),
    "delta_per":  ("δ Персея",           55.731,  47.788,  3.01),
    "gamma_per":  ("γ Персея",           46.199,  53.506,  2.90),
    "menkalinan": ("Менкалинан",         89.882,  44.948,  1.90),
    "theta_aur":  ("θ Возничего",        89.930,  37.213,  2.60),
    "iota_aur":   ("ι Возничего",        74.248,  33.166,  2.69),
    "izar":       ("Изар",              221.247,  27.074,  2.70),
    "seginus":    ("Сегин Волопаса",    218.019,  38.308,  3.03),
    "nekkar":     ("Неккар",            225.487,  40.391,  3.50),
    "muphrid":    ("Мюфрид",            208.671,  18.398,  2.68),
    "rho_boo":    ("ρ Волопаса",        217.957,  30.371,  3.60),
    "porrima":    ("Поррима",           190.415,  -1.449,  2.74),
    "vindemiatrix": ("Виндемиатрикс",   195.544,  10.959,  2.83),
    "zavijava":   ("Завиджава",         177.674,   1.765,  3.60),
    "heze":       ("Хезе",              203.673,  -0.596,  3.37),
    "zubeneschamali": ("Зубенешемали",  229.252,  -9.383,  2.61),
    "zubenelgenubi": ("Зубенельгенуби", 222.720, -16.042,  2.75),
    "zubenelhakrabi": ("Зубенельхакраби", 233.882, -14.790, 3.90),
    "sigma_lib":  ("σ Весов",           226.017, -25.282,  3.30),
    "kaus_australis": ("Каус Аустралис", 276.043, -34.385, 1.85),
    "kaus_media": ("Каус Медиа",        275.249, -29.828,  2.70),
    "kaus_borealis": ("Каус Бореалис",  276.993, -25.422,  2.80),
    "alnasl":     ("Альнасль",          271.452, -30.424,  2.99),
    "nunki":      ("Нунки",             283.816, -26.297,  2.05),
    "ascella":    ("Аскелла",           285.653, -29.880,  2.60),
    "tau_sgr":    ("τ Стрельца",        286.735, -27.670,  3.30),
    "phi_sgr":    ("φ Стрельца",        281.414, -26.991,  3.17),
    "algedi":     ("Альгеди",           304.514, -12.545,  3.57),
    "dabih":      ("Дабих",             305.253, -14.781,  3.05),
    "psi_cap":    ("ψ Козерога",        311.934, -25.270,  4.10),
    "omega_cap":  ("ω Козерога",        312.955, -26.919,  4.10),
    "zeta_cap":   ("ζ Козерога",        321.667, -22.411,  3.74),
    "nashira":    ("Нашира",            325.023, -16.662,  3.68),
    "deneb_algedi": ("Денеб Альгеди",   326.760, -16.127,  2.87),
    "hamal":      ("Гамаль",             31.793,  23.463,  2.00),
    "sheratan":   ("Шератан",            28.660,  20.808,  2.64),
    "mesarthim":  ("Месартим",           28.383,  19.294,  3.90),
    "eta_leo":    ("η Льва",            151.833,  16.763,  3.50),
    "adhafera":   ("Адхафера",          154.173,  23.417,  3.44),
    "rasalas":    ("Расалас",           148.191,  26.007,  3.88),
    "eps_leo":    ("ε Льва",            146.463,  23.774,  2.98),
    "zosma":      ("Зосма",             168.527,  20.524,  2.56),
    "chertan":    ("Чертан",            168.560,  15.430,  3.30),
    "kornephoros": ("Корнефорос",       247.555,  21.490,  2.77),
    "zeta_her":   ("ζ Геркулеса",       250.322,  31.603,  2.81),
    "eta_her":    ("η Геркулеса",       250.724,  38.922,  3.50),
    "eps_her":    ("ε Геркулеса",       255.073,  30.926,  3.92),
    "pi_her":     ("π Геркулеса",       258.762,  36.809,  3.16),
    "delta_her":  ("δ Геркулеса",       258.758,  24.839,  3.14),
    "rasalgethi": ("Рас Альгети",       258.662,  14.390,  3.00),
    "alphecca":   ("Альфекка",          233.672,  26.715,  2.23),
    "beta_crb":   ("β Сев. Короны",     231.957,  29.106,  3.68),
    "theta_crb":  ("θ Сев. Короны",     233.232,  31.359,  4.14),
    "gamma_crb":  ("γ Сев. Короны",     235.686,  26.296,  3.84),
    "delta_crb":  ("δ Сев. Короны",     237.185,  26.068,  4.60),
    "eps_crb":    ("ε Сев. Короны",     239.397,  26.878,  4.15),
    "alderamin":  ("Альдерамин",        319.645,  62.586,  2.45),
    "alfirk":     ("Альфирк",           322.165,  70.561,  3.23),
    "errai":      ("Эрраи",             354.837,  77.632,  3.21),
    "iota_cep":   ("ι Цефея",           342.420,  66.200,  3.50),
    "zeta_cep":   ("ζ Цефея",           332.714,  58.201,  3.35),
    "menkent":    ("Менкент",           211.671, -36.370,  2.06),
    "eps_cen":    ("ε Центавра",        204.972, -53.466,  2.30),
}


# Созвездия: название -> пары звёзд, соединённые линиями
CONSTELLATIONS = {
    "Орион": [
        ("betelgeuse", "bellatrix"), ("betelgeuse", "alnitak"),
        ("bellatrix", "mintaka"), ("alnitak", "alnilam"),
        ("alnilam", "mintaka"), ("alnitak", "saiph"),
        ("mintaka", "rigel"), ("rigel", "saiph"),
    ],
    "Большая Медведица": [
        ("dubhe", "merak"), ("merak", "phecda"), ("phecda", "megrez"),
        ("megrez", "dubhe"), ("megrez", "alioth"),
        ("alioth", "mizar"), ("mizar", "alkaid"),
    ],
    "Малая Медведица": [
        ("polaris", "yildun"), ("yildun", "eps_umi"), ("eps_umi", "zeta_umi"),
        ("zeta_umi", "eta_umi"), ("eta_umi", "pherkad"), ("pherkad", "kochab"),
        ("kochab", "zeta_umi"),
    ],
    "Кассиопея": [
        ("caph", "schedar"), ("schedar", "gamma_cas"),
        ("gamma_cas", "ruchbah"), ("ruchbah", "segin"),
    ],
    "Цефей": [
        ("alderamin", "alfirk"), ("alfirk", "errai"), ("errai", "iota_cep"),
        ("iota_cep", "zeta_cep"), ("zeta_cep", "alderamin"),
    ],
    "Южный Крест": [("acrux", "gacrux"), ("mimosa", "delta_cru")],
    "Центавр": [("rigil", "hadar"), ("hadar", "eps_cen"), ("hadar", "menkent")],
    "Лебедь": [
        ("deneb", "sadr"), ("sadr", "albireo"),
        ("gienah", "sadr"), ("sadr", "delta_cyg"),
    ],
    "Лира": [
        ("vega", "zeta_lyr"), ("zeta_lyr", "delta_lyr"), ("delta_lyr", "sulafat"),
        ("sulafat", "sheliak"), ("sheliak", "zeta_lyr"),
    ],
    "Орёл": [
        ("tarazed", "altair"), ("altair", "alshain"),
        ("altair", "delta_aql"), ("delta_aql", "lambda_aql"),
    ],
    "Лев": [
        ("regulus", "eta_leo"), ("eta_leo", "algieba"), ("algieba", "adhafera"),
        ("adhafera", "rasalas"), ("rasalas", "eps_leo"),
        ("algieba", "zosma"), ("zosma", "denebola"), ("zosma", "chertan"),
        ("chertan", "denebola"), ("chertan", "regulus"),
    ],
    "Близнецы": [
        ("castor", "mebsuta"), ("mebsuta", "tejat"), ("tejat", "propus"),
        ("pollux", "wasat"), ("wasat", "alhena"), ("mebsuta", "wasat"),
    ],
    "Телец": [
        ("zeta_tau", "aldebaran"), ("aldebaran", "theta_tau"),
        ("theta_tau", "gamma_tau"), ("gamma_tau", "delta_tau"),
        ("delta_tau", "eps_tau"), ("eps_tau", "elnath"),
    ],
    "Возничий": [
        ("capella", "menkalinan"), ("menkalinan", "theta_aur"),
        ("theta_aur", "elnath"), ("elnath", "iota_aur"), ("iota_aur", "capella"),
    ],
    "Большой Пёс": [
        ("mirzam", "sirius"), ("sirius", "wezen"), ("wezen", "adhara"),
        ("wezen", "aludra"), ("adhara", "furud"),
    ],
    "Малый Пёс": [("procyon", "gomeisa")],
    "Персей": [
        ("mirfak", "algol"), ("mirfak", "gamma_per"), ("mirfak", "delta_per"),
        ("delta_per", "eps_per"), ("eps_per", "zeta_per"),
    ],
    "Пегас": [
        ("markab", "scheat"), ("scheat", "alpheratz"),
        ("alpheratz", "algenib"), ("algenib", "markab"),
    ],
    "Андромеда": [
        ("alpheratz", "delta_and"), ("delta_and", "mirach"), ("mirach", "almach"),
    ],
    "Овен": [("hamal", "sheratan"), ("sheratan", "mesarthim")],
    "Волопас": [
        ("arcturus", "muphrid"), ("arcturus", "izar"), ("izar", "rho_boo"),
        ("arcturus", "rho_boo"), ("rho_boo", "seginus"), ("seginus", "nekkar"),
    ],
    "Северная Корона": [
        ("theta_crb", "beta_crb"), ("beta_crb", "alphecca"), ("alphecca", "gamma_crb"),
        ("gamma_crb", "delta_crb"), ("delta_crb", "eps_crb"),
    ],
    "Геркулес": [
        ("zeta_her", "eta_her"), ("eta_her", "pi_her"), ("pi_her", "eps_her"),
        ("eps_her", "zeta_her"), ("zeta_her", "kornephoros"),
        ("eps_her", "delta_her"), ("delta_her", "rasalgethi"),
    ],
    "Дева": [
        ("zavijava", "porrima"), ("porrima", "vindemiatrix"),
        ("porrima", "heze"), ("heze", "spica"),
    ],
    "Весы": [
        ("zubenelgenubi", "zubeneschamali"), ("zubeneschamali", "zubenelhakrabi"),
        ("zubenelhakrabi", "sigma_lib"), ("sigma_lib", "zubenelgenubi"),
    ],
    "Скорпион": [
        ("graffias", "dschubba"), ("dschubba", "pi_sco"), ("dschubba", "sigma_sco"),
        ("sigma_sco", "antares"), ("antares", "tau_sco"), ("tau_sco", "eps_sco"),
        ("eps_sco", "mu_sco"), ("mu_sco", "zeta_sco"), ("zeta_sco", "eta_sco"),
        ("eta_sco", "sargas"), ("sargas", "iota_sco"), ("iota_sco", "kappa_sco"),
        ("kappa_sco", "shaula"),
    ],
    "Стрелец": [
        ("alnasl", "kaus_media"), ("kaus_media", "kaus_borealis"),
        ("kaus_borealis", "phi_sgr"), ("phi_sgr", "nunki"), ("nunki", "tau_sgr"),
        ("tau_sgr", "ascella"), ("ascella", "kaus_australis"),
        ("kaus_australis", "alnasl"), ("kaus_media", "kaus_australis"),
        ("phi_sgr", "ascella"),
    ],
    "Козерог": [
        ("algedi", "dabih"), ("dabih", "psi_cap"), ("psi_cap", "omega_cap"),
        ("omega_cap", "zeta_cap"), ("zeta_cap", "deneb_algedi"),
        ("deneb_algedi", "nashira"), ("nashira", "algedi"),
    ],
}

# ключ astropy, подпись, цвет, размер маркера
PLANETS = [
    ("sun",     "Солнце",   "#FFD43B", 18),
    ("moon",    "Луна",     "#E9ECEF", 15),
    ("mercury", "Меркурий", "#ADB5BD", 8),
    ("venus",   "Венера",   "#FFE8A3", 11),
    ("mars",    "Марс",     "#FF6B4A", 10),
    ("jupiter", "Юпитер",   "#F4C58A", 13),
    ("saturn",  "Сатурн",   "#E3C78A", 12),
    ("uranus",  "Уран",     "#7FE0E6", 8),
    ("neptune", "Нептун",   "#6C8CFF", 8),
]




@lru_cache(maxsize=1)
def load_stars():
    """Каталог звёзд как numpy-массивы (читается один раз)."""
    keys = list(STARS)
    return {
        "keys": keys,
        "index": {k: i for i, k in enumerate(keys)},
        "name": np.array([STARS[k][0] for k in keys]),
        "ra": np.array([STARS[k][1] for k in keys], dtype=float),
        "dec": np.array([STARS[k][2] for k in keys], dtype=float),
        "mag": np.array([STARS[k][3] for k in keys], dtype=float),
    }


@lru_cache(maxsize=1)
def load_constellations():
    """
    Линии созвездий как индексы звёзд.
    Возвращает: names (список), seg_a, seg_b (индексы концов отрезков),
    members (для каждого созвездия — индексы его звёзд, для подписи).
    """
    idx = load_stars()["index"]
    names, seg_a, seg_b, members = [], [], [], []
    for cname, pairs in CONSTELLATIONS.items():
        names.append(cname)
        ids = set()
        for a, b in pairs:
            seg_a.append(idx[a])
            seg_b.append(idx[b])
            ids.update((idx[a], idx[b]))
        members.append(sorted(ids))
    return names, np.array(seg_a), np.array(seg_b), members


# ============================================================================
# 2. АСТРОНОМИЯ (Astropy + numpy)
# ============================================================================

# Без интернета: не качаем таблицы IERS
try:
    iers.conf.auto_download = False
    iers.conf.iers_degraded_accuracy = "warn"
except Exception:
    pass


def local_sidereal_deg(t, lon_deg):
    """Местное звёздное время, градусы."""
    try:
        return float(t.sidereal_time("mean", longitude=lon_deg * u.deg).deg)
    except Exception:
        d = t.jd - 2451545.0     # запасной вариант: приближённая формула GMST
        return float((280.46061837 + 360.98564736629 * d + lon_deg) % 360.0)


def transform_to_altaz(ra_deg, dec_deg, dt, lat, lon):
    """RA/Dec (градусы, ICRS/J2000) -> (высота°, азимут° от севера через восток)."""
    ra = np.radians(np.atleast_1d(np.asarray(ra_deg, dtype=float)))
    dec = np.radians(np.atleast_1d(np.asarray(dec_deg, dtype=float)))
    phi = np.radians(lat)
    h = np.radians(local_sidereal_deg(Time(dt), lon)) - ra          # часовой угол
    east = -np.cos(dec) * np.sin(h)
    north = np.sin(dec) * np.cos(phi) - np.cos(dec) * np.cos(h) * np.sin(phi)
    up = np.sin(dec) * np.sin(phi) + np.cos(dec) * np.cos(h) * np.cos(phi)
    alt = np.degrees(np.arcsin(np.clip(up, -1, 1)))
    az = np.degrees(np.arctan2(east, north)) % 360.0
    return alt, az


def alt_az_to_xyz(alt_deg, az_deg, r=1.0):
    """Высота/азимут -> (x=Восток, y=Север, z=Зенит) на сфере радиуса r."""
    alt = np.radians(np.asarray(alt_deg, dtype=float))
    az = np.radians(np.asarray(az_deg, dtype=float))
    return (r * np.cos(alt) * np.sin(az),
            r * np.cos(alt) * np.cos(az),
            r * np.sin(alt))


def get_planets(dt, lat, lon):
    """
    Солнце, Луна и планеты для момента dt и точки (lat, lon).
    Возвращает список dict: name, alt, az, mag (None), color, size.
    Для Луны учитывается параллакс (положение с поверхности Земли).
    """
    t = Time(dt)
    try:
        loc = EarthLocation.from_geodetic(lon * u.deg, lat * u.deg)
    except Exception:
        loc = None
    result = []
    with solar_system_ephemeris.set("builtin"):
        for key, name, color, size in PLANETS:
            try:
                try:
                    c = get_body(key, t, loc) if loc is not None else get_body(key, t)
                except Exception:
                    c = get_body(key, t)
                alt, az = transform_to_altaz(c.ra.deg, c.dec.deg, dt, lat, lon)
                result.append({"name": name, "alt": float(alt[0]), "az": float(az[0]),
                               "mag": None, "color": color, "size": size})
            except Exception:
                continue    # одно тело не посчиталось — остальные рисуем
    return result


def ecliptic_radec(n=361):
    lam = np.linspace(0, 360, n) * u.deg
    c = SkyCoord(lon=lam, lat=0 * u.deg, frame=BarycentricMeanEcliptic).icrs
    return c.ra.deg, c.dec.deg


def galactic_plane_radec(n=361):
    l = np.linspace(0, 360, n) * u.deg
    c = SkyCoord(l=l, b=0 * u.deg, frame="galactic").icrs
    return c.ra.deg, c.dec.deg


# ============================================================================
# 3. КАРТА НЕБА — вид ИЗНУТРИ небесной сферы (Plotly 3D)
# ============================================================================
#   Наблюдатель стоит в центре сферы (0, 0, 0) и смотрит наружу, на небо.
#   Камера Plotly — это маленький вектор «eye» вокруг центра: направление
#   взгляда = −eye, поэтому перетаскивание мышкой поворачивает голову.
#   Оси: x = Восток, y = Север, z = Зенит. Небо — сфера радиуса 1.

DEFAULT_LAT = 55.75    # Москва (точку по умолчанию уточнить у заказчика)
DEFAULT_LON = 37.62

LABEL_MAG = 1.5        # подписываем звёзды ярче этой величины
MOON_R = 0.05          # угловой радиус Луны на сфере (увеличен для читаемости)

# цвета неба (фон сцены): ночь -> сумерки -> день, по высоте Солнца
SKY_NIGHT, SKY_TWILIGHT, SKY_DAY = (3, 6, 18), (24, 44, 86), (64, 128, 196)

# начальный взгляд: на юг, 30° над горизонтом; |eye| = 0.05 — камера у центра
LOOK_DEFAULT = np.array([0.0, -np.cos(np.radians(30)), np.sin(np.radians(30))])
EYE_DIST = 0.05


# ------------------------------------------------------------------ утилиты
def _sky_color(sun_alt):
    """Цвет неба: ночь / сумерки / день в зависимости от высоты Солнца."""
    if sun_alt is None or sun_alt <= -12:
        c = SKY_NIGHT
    elif sun_alt <= 0:
        k = (sun_alt + 12) / 12
        c = [a + (b - a) * k for a, b in zip(SKY_NIGHT, SKY_TWILIGHT)]
    else:
        k = min(sun_alt / 25, 1)
        c = [a + (b - a) * k for a, b in zip(SKY_TWILIGHT, SKY_DAY)]
    return "rgb(%d,%d,%d)" % tuple(int(v) for v in c)


def _line(x, y, z, color, width=2, name="", dash=None):
    line = dict(color=color, width=width)
    if dash:
        line["dash"] = dash
    return go.Scatter3d(x=x, y=y, z=z, mode="lines", line=line,
                        hoverinfo="skip", name=name)


def _radec_line(ra, dec, dt, lat, lon, color, width, name, dash=None):
    alt, az = transform_to_altaz(ra, dec, dt, lat, lon)
    x, y, z = alt_az_to_xyz(alt, az)
    return _line(x, y, z, color, width, name, dash)


# ------------------------------------------------------------------ слои
def _ground_traces():
    """Земля (диск горизонта) + кромка горизонта + стороны света и зенит."""
    n = 90
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ground = go.Mesh3d(
        x=np.r_[0, np.sin(a)], y=np.r_[0, np.cos(a)], z=np.zeros(n + 1),
        i=np.zeros(n, dtype=int), j=np.arange(1, n + 1),
        k=np.r_[np.arange(2, n + 1), 1],
        color="#2B2E33", opacity=0.92, flatshading=True,
        lighting=dict(ambient=1, diffuse=0, specular=0),
        hoverinfo="skip", name="Земля")

    az = np.linspace(0, 360, 181)
    hx, hy, hz = alt_az_to_xyz(np.zeros_like(az), az)
    rim = _line(hx, hy, hz, "#D8E6F5", 3, "Горизонт")

    # подписи чуть выше горизонта, чтобы не прятались за диском земли
    dirs = {"С": 0, "СВ": 45, "В": 90, "ЮВ": 135, "Ю": 180, "ЮЗ": 225, "З": 270, "СЗ": 315}
    lx, ly, lz = alt_az_to_xyz(np.full(len(dirs), 4.0), np.array(list(dirs.values())))
    labels = go.Scatter3d(
        x=lx, y=ly, z=lz, mode="text", text=list(dirs),
        textfont=dict(color="#FFFFFF", size=15), hoverinfo="skip", name="Стороны света")
    deg = [d for d in range(0, 360, 30) if d % 45]
    dx, dy, dz = alt_az_to_xyz(np.full(len(deg), 1.5), np.array(deg, dtype=float))
    degs = go.Scatter3d(x=dx, y=dy, z=dz, mode="text", text=[f"{d}°" for d in deg],
                        textfont=dict(color="#FFE066", size=11),
                        hoverinfo="skip", name="Азимут")
    al = [30, 60]
    ax_, ay_, az_ = alt_az_to_xyz(np.array(al * 2, dtype=float),
                                  np.array([0.0] * 2 + [180.0] * 2))
    alts = go.Scatter3d(x=ax_, y=ay_, z=az_, mode="text", text=[f"{a}°" for a in al * 2],
                        textfont=dict(color="#FFE066", size=11),
                        hoverinfo="skip", name="Высота")
    zen = go.Scatter3d(x=[0], y=[0], z=[1], mode="markers+text", text=["Зенит"],
                       textposition="top center",
                       marker=dict(size=4, color="rgba(255,255,255,0.7)"),
                       textfont=dict(color="rgba(255,255,255,0.8)", size=11),
                       hoverinfo="skip", name="Зенит")
    return [ground, rim, labels, degs, alts, zen]


def _grid_trace():
    """Сетка Alt/Az: параллели через 30° и меридианы через 30°."""
    xs, ys, zs = [], [], []
    az = np.linspace(0, 360, 181)
    for alt in (-60, -30, 30, 60):
        x, y, z = alt_az_to_xyz(np.full_like(az, alt), az)
        xs += list(x) + [None]; ys += list(y) + [None]; zs += list(z) + [None]
    alts = np.linspace(-90, 90, 61)
    for a in range(0, 360, 30):
        x, y, z = alt_az_to_xyz(alts, np.full_like(alts, a))
        xs += list(x) + [None]; ys += list(y) + [None]; zs += list(z) + [None]
    return _line(xs, ys, zs, "rgba(170,200,230,0.30)", 1, "Сетка")


def _stars_traces(dt, lat, lon, with_names, dim):
    st = load_stars()
    alt, az = transform_to_altaz(st["ra"], st["dec"], dt, lat, lon)
    x, y, z = alt_az_to_xyz(alt, az)
    sizes = np.clip(7.5 - 1.5 * st["mag"], 2.5, 11)
    hover = np.array([f"{n} · {m:+.2f}m · выс {a:.0f}°"
                      for n, m, a in zip(st["name"], st["mag"], alt)])
    labels = np.where((st["mag"] <= LABEL_MAG) & with_names, st["name"], "")
    out = []
    for mask, color, op, nm in ((alt >= 0, "#FFFFFF", 0.95 * dim, "Звёзды"),
                                (alt < 0, "#8FA3B8", 0.45 * dim, "Звёзды под горизонтом")):
        out.append(go.Scatter3d(
            x=x[mask], y=y[mask], z=z[mask], mode="markers+text",
            marker=dict(size=sizes[mask], color=color, opacity=op, line=dict(width=0)),
            text=labels[mask], textposition="top center",
            textfont=dict(color="#CFE8FF", size=10),
            hovertext=hover[mask], hoverinfo="text", name=nm))
    return out


def _constellation_lines_trace(dt, lat, lon, n_pts=9):
    """Все отрезки созвездий одним трейсом; дуги большого круга, NaN между ними."""
    st = load_stars()
    _, ia, ib, _ = load_constellations()
    alt, az = transform_to_altaz(st["ra"], st["dec"], dt, lat, lon)
    xyz = np.stack(alt_az_to_xyz(alt, az), axis=1)             # (N, 3)
    va, vb = xyz[ia], xyz[ib]                                  # (S, 3)
    t = np.linspace(0, 1, n_pts)[None, :, None]
    pts = (1 - t) * va[:, None, :] + t * vb[:, None, :]        # (S, n_pts, 3)
    pts /= np.linalg.norm(pts, axis=2, keepdims=True)
    gap = np.full((pts.shape[0], 1, 3), np.nan)                # разрыв между отрезками
    pts = np.concatenate([pts, gap], axis=1).reshape(-1, 3)
    return _line(pts[:, 0], pts[:, 1], pts[:, 2], "rgba(130,210,255,0.7)", 2, "Созвездия")


def _constellation_labels_trace(dt, lat, lon):
    st = load_stars()
    names, _, _, members = load_constellations()
    alt, az = transform_to_altaz(st["ra"], st["dec"], dt, lat, lon)
    xyz = np.stack(alt_az_to_xyz(alt, az), axis=1)
    cent = np.array([xyz[m].mean(axis=0) for m in members])
    cent = cent / np.linalg.norm(cent, axis=1, keepdims=True)
    return go.Scatter3d(x=cent[:, 0], y=cent[:, 1], z=cent[:, 2], mode="text",
                        text=names, textfont=dict(color="rgba(130,210,255,0.9)", size=11),
                        hoverinfo="skip", name="Названия созвездий")


def _moon_traces(moon, sun):
    """
    Луна с фазой на поверхности сферы: тёмный диск + освещённая часть
    (полоска между краем диска и терминатором). Возвращает (traces, illum).
    """
    v = np.array(alt_az_to_xyz(moon["alt"], moon["az"])).ravel()
    vs = np.array(alt_az_to_xyz(sun["alt"], sun["az"])).ravel()
    cos_psi = float(np.clip(np.dot(v, vs), -1, 1))      # косинус элонгации
    illum = (1 - cos_psi) / 2

    # ось d — касательная к сфере, в сторону Солнца; p — перпендикуляр к ней
    d = vs - np.dot(vs, v) * v
    nd = np.linalg.norm(d)
    if nd < 1e-9:                                       # Солнце и Луна совпали
        d = np.cross(v, [0.0, 0.0, 1.0])
        nd = np.linalg.norm(d) or 1.0
    d = d / nd
    p = np.cross(v, d)

    def at(cx, cy):                                      # точка на касательной плоскости
        return v[None, :] + MOON_R * (np.outer(cx, d) + np.outer(cy, p))

    # тёмный диск (веер из центра)
    n = 48
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = at(np.cos(a), np.sin(a))
    pts = np.vstack([v, ring])
    disk = go.Mesh3d(
        x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
        i=np.zeros(n, dtype=int), j=np.arange(1, n + 1), k=np.r_[np.arange(2, n + 1), 1],
        color="#3A4458", flatshading=True,
        lighting=dict(ambient=1, diffuse=0, specular=0),
        hoverinfo="skip", name="Луна (тень)")

    # освещённая часть: лента между краем (сторона Солнца) и терминатором
    m = 25
    th = np.linspace(-np.pi / 2, np.pi / 2, m)
    limb = at(np.cos(th), np.sin(th))
    term = at(cos_psi * np.cos(th), np.sin(th))
    lp = np.vstack([limb, term]) * 0.992                 # чуть ближе к наблюдателю
    ti, tj, tk = [], [], []
    for s in range(m - 1):
        ti += [s, s + 1];      tj += [s + 1, m + s + 1]; tk += [m + s, m + s]
    light = go.Mesh3d(
        x=lp[:, 0], y=lp[:, 1], z=lp[:, 2], i=ti, j=tj, k=tk,
        color="#F1F3F5", flatshading=True,
        lighting=dict(ambient=1, diffuse=0, specular=0),
        hoverinfo="skip", name="Луна (свет)")

    label = go.Scatter3d(
        x=[v[0]], y=[v[1]], z=[v[2]], mode="markers+text",
        marker=dict(size=14, color="rgba(0,0,0,0)"),
        text=["Луна"], textposition="bottom center",
        textfont=dict(color="white", size=11),
        hovertext=[f"Луна: высота {moon['alt']:+.1f}°, азимут {moon['az']:.1f}°, "
                   f"освещено {illum * 100:.0f}%"],
        hoverinfo="text", name="Луна")
    return [disk, light, label], illum


def _planets_traces(planets):
    """Солнце и планеты. Луну рисует _moon_traces."""
    out = []
    for p in planets:
        if p["name"] == "Луна":
            continue
        v = np.array(alt_az_to_xyz(p["alt"], p["az"])).ravel()
        if p["name"] == "Солнце":       # мягкое свечение вокруг диска
            out.append(go.Scatter3d(
                x=[v[0]], y=[v[1]], z=[v[2]], mode="markers",
                marker=dict(size=p["size"] * 2.4, color=p["color"], opacity=0.2),
                hoverinfo="skip", name="Свечение"))
        out.append(go.Scatter3d(
            x=[v[0]], y=[v[1]], z=[v[2]], mode="markers+text",
            marker=dict(size=p["size"], color=p["color"],
                        opacity=1.0 if p["alt"] >= 0 else 0.55,
                        line=dict(color="white", width=1)),
            text=[p["name"]], textposition="bottom center",
            textfont=dict(color="white", size=11),
            hovertext=[f"{p['name']}: высота {p['alt']:+.1f}°, азимут {p['az']:.1f}°"],
            hoverinfo="text", name=p["name"]))
    return out


def _pole_traces(lat):
    """Полюса мира — точки на сфере в направлении оси вращения Земли."""
    p = np.array([0.0, np.cos(np.radians(lat)), np.sin(np.radians(lat))])
    return go.Scatter3d(
        x=[p[0], -p[0]], y=[p[1], -p[1]], z=[p[2], -p[2]],
        mode="markers+text", text=["Север мира", "Юг мира"],
        textposition="top center", textfont=dict(color="#FFB0B0", size=10),
        marker=dict(size=5, color=["#FF4D4D", "#3D7BFF"], symbol="diamond"),
        hovertext=["Северный полюс мира", "Южный полюс мира"],
        hoverinfo="text", name="Полюса")


# ------------------------------------------------------------------ сборка
def build_sky_figure(dt, lat, lon, layers):
    """
    dt     — момент времени (datetime, UTC)
    layers — множество: stars, names, const, const_names, planets,
             grid, ecliptic, equator, milky
    Возвращает (figure, info_str). Камера стоит внутри сферы (в её центре).
    """
    layers = set(layers or [])
    planets = get_planets(dt, lat, lon)
    sun = next((p for p in planets if p["name"] == "Солнце"), None)
    moon = next((p for p in planets if p["name"] == "Луна"), None)
    sun_alt = sun["alt"] if sun else None
    dim = 1.0 if sun_alt is None else float(np.clip((6 - sun_alt) / 18, 0.35, 1.0))
    sky = _sky_color(sun_alt)

    fig = go.Figure()
    for tr in _ground_traces():
        fig.add_trace(tr)
    if "grid" in layers:
        fig.add_trace(_grid_trace())
    if "equator" in layers:
        ra = np.linspace(0, 360, 361)
        fig.add_trace(_radec_line(ra, np.zeros_like(ra), dt, lat, lon,
                                  "#5BC8F5", 3, "Небесный экватор"))
    if "ecliptic" in layers:
        ra, dec = ecliptic_radec()
        fig.add_trace(_radec_line(ra, dec, dt, lat, lon, "#FFD43B", 4, "Эклиптика"))
    if "milky" in layers:
        ra, dec = galactic_plane_radec()
        fig.add_trace(_radec_line(ra, dec, dt, lat, lon,
                                  "rgba(190,170,255,0.45)", 10, "Млечный Путь"))

    fig.add_trace(_pole_traces(lat))

    if "const" in layers:
        fig.add_trace(_constellation_lines_trace(dt, lat, lon))
    if "const_names" in layers:
        fig.add_trace(_constellation_labels_trace(dt, lat, lon))
    if "stars" in layers:
        for tr in _stars_traces(dt, lat, lon, with_names="names" in layers, dim=dim):
            fig.add_trace(tr)

    illum = None
    if moon and sun:
        if "planets" in layers:
            traces, illum = _moon_traces(moon, sun)
            for tr in traces:
                fig.add_trace(tr)
        else:
            vm = np.array(alt_az_to_xyz(moon["alt"], moon["az"])).ravel()
            vs = np.array(alt_az_to_xyz(sun["alt"], sun["az"])).ravel()
            illum = (1 - float(np.clip(np.dot(vm, vs), -1, 1))) / 2
    if "planets" in layers:
        for tr in _planets_traces(planets):
            fig.add_trace(tr)

    axis = dict(visible=False, range=[-1.45, 1.45], showbackground=False)
    eye = -EYE_DIST * LOOK_DEFAULT          # камера в центре сферы, взгляд на юг
    fig.update_layout(
        paper_bgcolor=sky, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
        uirevision="sky3d",                 # направление взгляда не сбрасывается между callback'ами
        scene=dict(
            xaxis=axis, yaxis=axis, zaxis=axis, aspectmode="cube", bgcolor=sky,
            domain=dict(x=[0, 1], y=[0, 1]),
            camera=dict(eye=dict(x=float(eye[0]), y=float(eye[1]), z=float(eye[2])),
                        center=dict(x=0, y=0, z=0), up=dict(x=0, y=0, z=1),
                        projection=dict(type="perspective")),
        ),
    )

    lst = local_sidereal_deg(Time(dt), lon)
    h, m = int(lst / 15), int((lst / 15 - int(lst / 15)) * 60)
    info = f"UTC: {dt.strftime('%Y-%m-%d %H:%M')} · Звёздное время: {h:02d}ч {m:02d}м"
    if moon:
        info += f" · Луна: выс {moon['alt']:+.1f}°, аз {moon['az']:.1f}°"
        if illum is not None:
            info += f", освещена {illum * 100:.0f}%"
    if sun:
        info += f" · Солнце: выс {sun['alt']:+.1f}°, аз {sun['az']:.1f}°"
    return fig, info


# ============================================================================
# 4. ИНТЕРФЕЙС И ПРИЛОЖЕНИЕ
# ============================================================================

# Базовая сетка и компоненты Bootstrap (DARKLY / FLATLY / CYBORG / MORPH)
BOOTSTRAP_THEME = dbc.themes.DARKLY

COLORS = {
    "bg":      "#E4F2FF",  # Основной фон всей страницы 
    "paper":   "#C6E7FF",  # Фон карточек, шапки и блоков
    "accent":  "#82D2FF",  # Акцентный цвет: кнопки, линии, загрузка
    "text":    "#1E2525",  # Основной цвет текста
    "muted":   "#2C2F32",  # Приглушенный текст: подсказки, подвал
    "border":  "#3A506B",  # Цвет рамок и разделителей
}

# Общие настройки геометрии и отступов
LAYOUT_STYLES = {
    "border_radius": "12px",
    "map_height": "620px",
    "font_family": "system-ui, -apple-system, 'Segoe UI', Montserrat, sans-serif",
}

# Готовые стили для карточек
CARD_STYLE = {
    "backgroundColor": COLORS["paper"],
    "borderColor": COLORS["border"],
    "color": COLORS["text"],
    "borderRadius": LAYOUT_STYLES["border_radius"],
}

INPUT_STYLE = {
    "backgroundColor": COLORS["bg"],
    "borderColor": COLORS["border"],
    "color": COLORS["text"],
}

# ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ

app = Dash(
    __name__,
    external_stylesheets=[BOOTSTRAP_THEME],
    title="AstroGuide",
    update_title=None,
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1"}],
)

# УТИЛИТЫ И ШАБЛОНЫ КОМПОНЕНТОВ

def make_empty_fig(text="Заглушка"):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["paper"],
        plot_bgcolor=COLORS["paper"],
        font=dict(color=COLORS["muted"], size=16, family=LAYOUT_STYLES["font_family"]),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    fig.add_annotation(
        text=text,
        showarrow=False,
        font=dict(size=20, color=COLORS["muted"]),
    )
    return fig

def section_title(text, id_):
    """Единый стиль заголовков для всех секций сайта"""
    return html.H2(
        text,
        id=id_,
        className="mb-4 pb-2 fw-bold",
        style={
            "color": COLORS["text"],
            "borderBottom": f"2px solid {COLORS['border']}",
        },
    )


# --- 1. Шапка ---------------------------------------------------------------
header = dbc.Navbar(
    dbc.Container([
        dbc.NavbarBrand(
            "🔭 AstroGuide",
            href="#top",
            style={"color": COLORS["text"], "fontWeight": "bold"},
        ),
        dbc.Nav([
            dbc.NavLink("Карта", href="#map", style={"color": COLORS["text"]}),
            dbc.NavLink("Нейросеть", href="#nn", style={"color": COLORS["text"]}),
            dbc.NavLink("О проекте", href="#about", style={"color": COLORS["text"]}),
        ], navbar=True),
    ]),
    color=COLORS["paper"],
    dark=True,
    className="mb-4 shadow-sm",
    style={"borderBottom": f"1px solid {COLORS['border']}"},id="top",
    sticky="top",
)

# --- 2. Карта неба ----------------------------------------------------
SKY_LAYER_OPTIONS = [
    {"label": "Планеты",             "value": "planets"},
    {"label": "Звёзды",              "value": "stars"},
    {"label": "Названия звёзд",      "value": "names"},
    {"label": "Созвездия",           "value": "const"},
    {"label": "Названия созвездий",  "value": "const_names"},
    {"label": "Сетка",               "value": "grid"},
    {"label": "Эклиптика",           "value": "ecliptic"},
    {"label": "Экватор",             "value": "equator"},
    {"label": "Млечный Путь",        "value": "milky"},
]
SKY_LAYERS_DEFAULT = ["planets", "stars", "names", "const", "grid", "ecliptic"]

# Слайдер времени: сдвиг от момента открытия страницы, минуты (0…+4 ч, шаг 30)
OFFSET_MAX, OFFSET_STEP = 240, 30
OFFSET_MARKS = {m: ("Сейчас" if m == 0 else f"+{m // 60}ч") for m in range(0, OFFSET_MAX + 1, 60)}

# Города для быстрого выбора: название -> (широта°, долгота°)
CITIES = {
    "Москва": (55.75, 37.62), "Санкт-Петербург": (59.94, 30.31),
    "Калининград": (54.71, 20.51), "Казань": (55.79, 49.12),
    "Нижний Новгород": (56.33, 44.00), "Екатеринбург": (56.84, 60.61),
    "Новосибирск": (55.03, 82.92), "Красноярск": (56.01, 92.85),
    "Иркутск": (52.29, 104.30), "Владивосток": (43.12, 131.89),
    "Сочи": (43.60, 39.73), "Мурманск": (68.97, 33.07),
    "Минск": (53.90, 27.57), "Киев": (50.45, 30.52), "Астана": (51.17, 71.43),
    "Лондон": (51.51, -0.13), "Нью-Йорк": (40.71, -74.01),
    "Токио": (35.68, 139.69), "Сидней": (-33.87, 151.21),
    "Кейптаун": (-33.92, 18.42), "Буэнос-Айрес": (-34.60, -58.38),
}
CITY_OPTIONS = ([{"label": "Свои координаты", "value": "custom"}] +
                [{"label": c, "value": c} for c in CITIES])

sky_controls = html.Div([
    dbc.Checklist(id="sky-layers", options=SKY_LAYER_OPTIONS,
                  value=SKY_LAYERS_DEFAULT, inline=True, switch=True, className="mb-3"),
    dbc.Row([
        dbc.Col([
            html.Div("Время: сдвиг вперёд от момента открытия", className="small mb-1",
                     style={"color": COLORS["muted"]}),
            dcc.Slider(id="sky-offset", min=0, max=OFFSET_MAX, step=OFFSET_STEP, value=0,
                       marks=OFFSET_MARKS, updatemode="mouseup",   # callback только при отпускании
                       tooltip={"placement": "bottom", "always_visible": False}),
        ], lg=5, md=12, className="mb-2"),
        dbc.Col([
            html.Div("Город", className="small mb-1", style={"color": COLORS["muted"]}),
            dbc.Select(id="sky-city", options=CITY_OPTIONS, value="Москва",
                       size="sm", style=INPUT_STYLE),
        ], lg=2, md=4, sm=12, className="mb-2"),
        dbc.Col(
            dbc.InputGroup([
                dbc.InputGroupText("Шир."),
                dbc.Input(id="sky-lat", type="number", value=DEFAULT_LAT, step=0.01,
                          style=INPUT_STYLE),
                dbc.InputGroupText("Долг."),
                dbc.Input(id="sky-lon", type="number", value=DEFAULT_LON, step=0.01,
                          style=INPUT_STYLE),
                dbc.Button("Применить", id="sky-apply", className="border-0",
                           style={"backgroundColor": COLORS["accent"], "color": "#000"}),
            ], size="sm"),
            lg=4, md=6, sm=12, className="mb-2",
        ),
        dbc.Col(
            dbc.Button("Сейчас", id="sky-now", size="sm", className="border-0 w-100",
                       style={"backgroundColor": COLORS["accent"], "color": "#000"}),
            lg=1, md=2, sm=12, className="mb-2",
        ),
    ], className="g-2 align-items-end"),
    html.Div(id="sky-error", className="small mb-1", style={"color": "#B00020"}),
])

map_section = dbc.Row(
    dbc.Col([
        section_title("Карта звёздного неба", "map"),
        dcc.Store(id="sky-t0"),       # момент открытия / нажатия «Сейчас» (ISO, UTC)
        dcc.Store(id="sky-coords"),   # применённые координаты {"lat","lon"}
        dbc.Card(
            dbc.CardBody([
                sky_controls,
                dcc.Loading(
                    dcc.Graph(
                        id="sky_map",
                        figure=make_empty_fig("Загрузка карты..."),
                        style={"height": LAYOUT_STYLES["map_height"]},
                        config={"displayModeBar": False},
                    ),
                    type="circle", color=COLORS["accent"],
                ),
                html.Small(id="sky-info", style={"color": COLORS["muted"]}),
                html.Div("Вы стоите в центре небесной сферы: зажмите кнопку мыши и тяните, "
                         "чтобы осмотреться. Серый диск — земля под горизонтом, цифры — "
                         "азимут и высота. Выберите город или введите координаты.",
                         className="small", style={"color": COLORS["muted"]}),
            ], className="p-3"),
            style=CARD_STYLE,
        ),
    ], width=12),
    className="mb-5",
)

# --- 3. Нейросеть -----------------------------------------------------------
nn_form_col = dbc.Col(
    dbc.Card(
        dbc.CardBody([
            dbc.Input(
                id="input-data",
                type="text",
                placeholder="Введите название или координаты...",
                className="mb-3",
                style=INPUT_STYLE,
            ),
            dbc.Button(
                "Отправить",
                id="submit-val",
                className="mb-3 border-0 fw-semibold",
                style={"backgroundColor": COLORS["accent"], "color": "#000"},
            ),
            html.Hr(style={"borderColor": COLORS["border"]}),
            html.Div(
                "Здесь появится результат обработки...",
                id="output-data",
                style={"color": COLORS["muted"]},
            ),
        ]),
        className="h-100",
        style=CARD_STYLE,
    ),
    lg=7, md=12,
)

nn_side_col = dbc.Col(
    dbc.Card(
        dbc.CardBody([
            html.H5("💡 Подсказка", className="card-title", style={"color": COLORS["accent"]}),
            html.P(
                "Введите имя объекта — например, «Сириус» или координаты прямого восхождения и склонения.",
                className="mb-0",
                style={"color": COLORS["muted"]},
            ),
        ]),
        className="h-100",
        style=CARD_STYLE,
    ),
    lg=5, md=12,
)

nn_section = html.Div([
    section_title("Нейросеть", "nn"),
    dbc.Alert(
        "Здесь будет нейросеть:).",
        color="info",
        className="mb-4",
    ),
    dbc.Row([nn_form_col, nn_side_col], className="g-4"),
], className="mb-5")

# --- 4. О проекте -----------------------------------------------------------
ABOUT_MD = """
**AstroGuide** — учебный проект на *Plotly Dash*.

- Интерактивная карта звёздного неба

Документация: [Dash Plotly](https://dash.plotly.com)
"""

about_section = dbc.Row(
    dbc.Col([
        section_title("О проекте", "about"),
        dbc.Card(
            dbc.CardBody(
                dcc.Markdown(ABOUT_MD, link_target="_blank", className="mb-0"),
            ),
            style=CARD_STYLE,
        ),
    ], lg=8, md=12),
    className="mb-5",
)

# --- 5. Подвал --------------------------------------------------------------
footer = dbc.Row(
    dbc.Col(
        html.Small(
            "© 2026 AstroGuide · учебный проект",
            style={"color": COLORS["muted"]},
        ),
        className="text-center py-4",
        style={"borderTop": f"1px solid {COLORS['border']}"},
    ),
)

app.layout = html.Div(
    [
        header,
        dbc.Container([
            map_section,
            nn_section,
            about_section,
            footer,
        ]),
    ],
    style={
        "backgroundColor": COLORS["bg"],
        "color": COLORS["text"],
        "minHeight": "100vh",
        "fontFamily": LAYOUT_STYLES["font_family"],
    },
)

@callback(
    Output("sky-t0", "data"),
    Output("sky-offset", "value"),
    Input("sky-now", "n_clicks"),
)
def reset_t0(_n):
    """При загрузке страницы и по «Сейчас»: t0 = сейчас; «Сейчас» ещё и сбрасывает слайдер."""
    t0 = datetime.now(timezone.utc).isoformat()
    if ctx.triggered_id == "sky-now":
        return t0, 0
    return t0, no_update


@callback(
    Output("sky-coords", "data"),
    Output("sky-error", "children"),
    Output("sky-lat", "value"),
    Output("sky-lon", "value"),
    Input("sky-apply", "n_clicks"),
    Input("sky-city", "value"),
    State("sky-lat", "value"),
    State("sky-lon", "value"),
)
def apply_coords(_n, city, lat, lon):
    """Город из списка или свои координаты; при ошибке показываем сообщение."""
    if ctx.triggered_id == "sky-city" and city in CITIES:
        lat, lon = CITIES[city]                       # выбор города подставляет координаты
        return {"lat": lat, "lon": lon}, "", lat, lon
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return no_update, "Широта и долгота должны быть числами.", no_update, no_update
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return no_update, "Широта: от −90 до 90, долгота: от −180 до 180.", no_update, no_update
    return {"lat": lat, "lon": lon}, "", no_update, no_update


@callback(
    Output("sky_map", "figure"),
    Output("sky-info", "children"),
    Input("sky-layers", "value"),
    Input("sky-offset", "value"),
    Input("sky-t0", "data"),
    Input("sky-coords", "data"),
)
def update_sky(layers, offset, t0, coords):
    if not t0 or not coords:
        raise PreventUpdate
    dt = datetime.fromisoformat(t0) + timedelta(minutes=offset or 0)
    started = time.perf_counter()
    fig, info = build_sky_figure(dt, coords["lat"], coords["lon"], layers)
    ms = (time.perf_counter() - started) * 1000
    return fig, f"{info} · сдвиг +{offset or 0} мин · расчёт {ms:.0f} мс"


@callback(
     Output("output-data", "children"),
    Input("submit-val", "n_clicks"),
    State("input-data", "value"),
    prevent_initial_call=True,
)
def process_input(n_clicks, value):
    if not value or not value.strip():
        return dbc.Alert(
            "Введите что-нибудь перед отправкой",
            color="warning",
            className="mb-0",
        )
    return dbc.Alert(
        f"Вы ввели: {value}",
        color="success",
        className="mb-0",
    )

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)