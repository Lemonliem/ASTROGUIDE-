"""
Каталог звёзд и стик-фигуры созвездий.

Источники:
  • Звёзды:    либо data/stars_hyg.parquet (см. scripts/fetch_hyg.py),
                либо встроенный набор ярких звёзд + синтетический добор.
  • Созвездия: встроенный набор реальных звёзд + линии (координаты
                сегментов сохраняются, чтобы не зависеть от каталога).
"""
from functools import lru_cache
from pathlib import Path

import numpy as np

from ..config import ALL_CONSTELLATIONS, MAJOR_CONSTELLATIONS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ── Встроенный набор ярких звёзд (реальные J2000, mag ≤ 2.5) ─────────────
_STARS = {
    "sirius":     (101.287, -16.716, -1.46),
    "canopus":    ( 95.988, -52.696, -0.74),
    "arcturus":   (213.915,  19.182, -0.05),
    "rigil":      (219.900, -60.834, -0.01),
    "vega":       (279.235,  38.784,  0.03),
    "capella":    ( 79.172,  45.998,  0.08),
    "rigel":      ( 78.634,  -8.202,  0.13),
    "procyon":    (114.825,   5.225,  0.34),
    "betelgeuse": ( 88.793,   7.407,  0.50),
    "achernar":   ( 24.429, -57.237,  0.46),
    "hadar":      (210.956, -60.373,  0.61),
    "altair":     (297.696,   8.868,  0.76),
    "acrux":      (186.650, -63.099,  0.76),
    "aldebaran":  ( 68.980,  16.509,  0.85),
    "spica":      (201.298, -11.161,  0.97),
    "antares":    (247.352, -26.432,  1.06),
    "pollux":     (116.329,  28.026,  1.14),
    "fomalhaut":  (344.413, -29.622,  1.16),
    "deneb":      (310.358,  45.280,  1.25),
    "mimosa":     (191.930, -59.689,  1.25),
    "regulus":    (152.093,  11.967,  1.35),
    "castor":     (113.650,  31.888,  1.58),
    "bellatrix":  ( 81.283,   6.350,  1.64),
    "gacrux":     (187.791, -57.113,  1.64),
    "elnath":     ( 81.573,  28.608,  1.65),
    "alnilam":    ( 84.053,  -1.202,  1.69),
    "alnitak":    ( 85.190,  -1.943,  1.77),
    "shaula":     (263.402, -37.104,  1.62),
    "dubhe":      (165.932,  61.751,  1.79),
    "alioth":     (193.507,  55.960,  1.77),
    "mirfak":     ( 51.081,  49.861,  1.80),
    "alkaid":     (206.885,  49.313,  1.86),
    "polaris":    ( 37.955,  89.264,  1.98),
    "mizar":      (200.981,  54.925,  2.04),
    "saiph":      ( 86.939,  -9.670,  2.06),
    "algieba":    (154.993,  19.842,  2.01),
    "denebola":   (177.265,  14.572,  2.14),
    "sadr":       (305.557,  40.257,  2.20),
    "mintaka":    ( 83.002,  -0.299,  2.23),
    "schedar":    ( 10.127,  56.537,  2.24),
    "caph":       (  2.295,  59.150,  2.27),
    "merak":      (165.460,  56.382,  2.37),
    "phecda":     (178.458,  53.695,  2.44),
    "gienah":     (311.553,  33.970,  2.50),
    "gamma_cas":  ( 14.177,  60.717,  2.47),
    "ruchbah":    ( 21.454,  60.235,  2.68),
    "segin":      ( 28.599,  63.670,  3.38), # ← ДОБАВЛЕНО
    "albireo":    (292.680,  27.960,  3.10), # ← ДОБАВЛЕНО
    "delta_cru":  (183.786, -58.749,  2.80),
    "delta_cyg":  (296.244,  45.131,  2.87),
    "megrez":     (183.857,  57.033,  3.31),
    # Центавр
    "eps_cen":    (204.972, -53.466,  2.30),
    "menkent":    (211.671, -36.370,  2.06),
    # Цефей
    "alderamin":  (319.645,  62.586,  2.45),
    "alfirk":     (322.165,  70.561,  3.23),
    "errai":      (354.837,  77.632,  3.21),
    "iota_cep":   (342.420,  66.200,  3.50),
    "zeta_cep":   (332.714,  58.201,  3.35),
    # Лира / Лебедь
    "sulafat":    (284.736,  32.690,  3.24),
    "sheliak":    (282.520,  33.363,  3.52),
    "delta_lyr":  (283.626,  36.899,  4.30),
    "zeta_lyr":   (281.194,  37.605,  4.36),
    # Орёл
    "tarazed":    (296.565,  10.613,  2.72),
    "alshain":    (298.828,   6.407,  3.71),
    "delta_aql":  (291.375,   3.115,  3.36),
    "lambda_aql": (286.562,  -4.883,  3.44),
    # Лев
    "eta_leo":    (151.833,  16.763,  3.50),
    "adhafera":   (154.173,  23.417,  3.44),
    "rasalas":    (148.191,  26.007,  3.88),
    "eps_leo":    (146.463,  23.774,  2.98),
    "zosma":      (168.527,  20.524,  2.56),
    "chertan":    (168.560,  15.430,  3.30),
    # Близнецы
    "mebsuta":    (100.983,  25.131,  3.06),
    "tejat":      ( 95.740,  22.514,  2.88),
    "propus":     ( 93.719,  22.507,  3.28),
    "wasat":      (110.031,  21.982,  3.53),
    "alhena":     ( 99.428,  16.399,  1.93),
    # Телец
    "zeta_tau":   ( 84.411,  21.143,  3.00),
    "theta_tau":  ( 67.166,  15.871,  3.40),
    "gamma_tau":  ( 64.948,  15.628,  3.65),
    "delta_tau":  ( 65.734,  17.543,  3.76),
    "eps_tau":    ( 67.154,  19.180,  3.53),
    # Возничий
    "menkalinan": ( 89.882,  44.948,  1.90),
    "theta_aur":  ( 89.930,  37.213,  2.60),
    "iota_aur":   ( 74.248,  33.166,  2.69),
    # Большой Пёс
    "mirzam":     ( 95.675, -17.956,  1.98),
    "adhara":     (104.656, -28.972,  1.50),
    "wezen":      (107.098, -26.393,  1.84),
    "aludra":     (111.024, -29.303,  2.45),
    "furud":      ( 95.078, -30.063,  3.00),
    # Малый Пёс
    "gomeisa":    (111.788,   8.289,  2.89),
    # Персей
    "algol":      ( 47.042,  40.956,  2.10),
    "gamma_per":  ( 46.199,  53.506,  2.90),
    "delta_per":  ( 55.731,  47.788,  3.01),
    "eps_per":    ( 59.464,  40.010,  2.89),
    "zeta_per":   ( 58.533,  31.884,  2.85),
    # Пегас
    "markab":     (346.190,  15.205,  2.49),
    "scheat":     (345.944,  28.083,  2.42),
    "algenib":    (  3.309,  15.184,  2.83),
    "alpheratz":  (  2.097,  29.091,  2.06),
    # Андромеда
    "mirach":     ( 17.433,  35.621,  2.06),
    "almach":     ( 30.975,  42.330,  2.26),
    "delta_and":  (  9.832,  30.861,  3.27),
    # Овен
    "hamal":      ( 31.793,  23.463,  2.00),
    "sheratan":   ( 28.660,  20.808,  2.64),
    "mesarthim":  ( 28.383,  19.294,  3.90),
    # Волопас
    "muphrid":    (208.671,  18.398,  2.68),
    "izar":       (221.247,  27.074,  2.70),
    "rho_boo":    (217.957,  30.371,  3.60),
    "seginus":    (218.019,  38.308,  3.03),
    "nekkar":     (225.487,  40.391,  3.50),
    # Сев. Корона
    "alphecca":   (233.672,  26.715,  2.23),
    "beta_crb":   (231.957,  29.106,  3.68),
    "theta_crb":  (233.232,  31.359,  4.14),
    "gamma_crb":  (235.686,  26.296,  3.84),
    "delta_crb":  (237.185,  26.068,  4.60),
    "eps_crb":    (239.397,  26.878,  4.15),
    # Геркулес
    "kornephoros":(247.555,  21.490,  2.77),
    "zeta_her":   (250.322,  31.603,  2.81),
    "eta_her":    (250.724,  38.922,  3.50),
    "eps_her":    (255.073,  30.926,  3.92),
    "pi_her":     (258.762,  36.809,  3.16),
    "delta_her":  (258.758,  24.839,  3.14),
    "rasalgethi": (258.662,  14.390,  3.00),
    # Дева
    "zavijava":   (177.674,   1.765,  3.60),
    "porrima":    (190.415,  -1.449,  2.74),
    "vindemiatrix":(195.544, 10.959,  2.83),
    "heze":       (203.673,  -0.596,  3.37),
    # Весы
    "zubeneschamali":(229.252,-9.383, 2.61),
    "zubenelgenubi":(222.720,-16.042, 2.75),
    "zubenelhakrabi":(233.882,-14.790,3.90),
    "sigma_lib":  (226.017, -25.282,  3.30),
    # Скорпион
    "dschubba":   (240.083, -22.622,  2.32),
    "graffias":   (241.359, -19.805,  2.62),
    "pi_sco":     (239.713, -26.114,  2.89),
    "sigma_sco":  (245.297, -25.593,  2.90),
    "tau_sco":    (248.971, -28.216,  2.82),
    "eps_sco":    (252.541, -34.293,  2.29),
    "mu_sco":     (252.968, -38.047,  3.00),
    "zeta_sco":   (253.499, -42.361,  3.62),
    "eta_sco":    (258.038, -43.239,  3.33),
    "sargas":     (264.330, -42.998,  1.87),
    "iota_sco":   (266.896, -40.127,  3.00),
    "kappa_sco":  (265.622, -39.030,  2.41),
    # Стрелец
    "alnasl":     (271.452, -30.424,  2.99),
    "kaus_media": (275.249, -29.828,  2.70),
    "kaus_borealis":(276.993,-25.422, 2.80),
    "phi_sgr":    (281.414, -26.991,  3.17),
    "nunki":      (283.816, -26.297,  2.05),
    "tau_sgr":    (286.735, -27.670,  3.30),
    "ascella":    (285.653, -29.880,  2.60),
    "kaus_australis":(276.043,-34.385,1.85),
    # Козерог
    "algedi":     (304.514, -12.545,  3.57),
    "dabih":      (305.253, -14.781,  3.05),
    "psi_cap":    (311.934, -25.270,  4.10),
    "omega_cap":  (312.955, -26.919,  4.10),
    "zeta_cap":   (321.667, -22.411,  3.74),
    "nashira":    (325.023, -16.662,  3.68),
    "deneb_algedi":(326.760,-16.127,  2.87),
    # Малая Медведица
    "kochab":     (222.676,  74.156,  2.08),
    "pherkad":    (230.182,  71.834,  3.05),
    "yildun":     (263.054,  86.586,  4.36),
    "eps_umi":    (251.493,  82.037,  4.20),
    "zeta_umi":   (236.015,  77.795,  4.30),
    "eta_umi":    (244.376,  75.755,  4.95),
}


# ── Стик-фигуры (по ключам встроенных звёзд) ────────────────────────────
_CONSTELLATION_LINES = {
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
        ("theta_crb", "beta_crb"), ("beta_crb", "alphecca"),
        ("alphecca", "gamma_crb"), ("gamma_crb", "delta_crb"),
        ("delta_crb", "eps_crb"),
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
        ("zubenelgenubi", "zubeneschamali"),
        ("zubeneschamali", "zubenelhakrabi"),
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


# ── Загрузка звёзд ──────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def load_stars() -> dict:
    """
    Возвращает словарь с массивами: ra, dec, mag (float, degrees / mag).
    Предпочтение: parquet с HYG (1600 звёзд mag ≤ 5.0).
    Запасной вариант: встроенный набор + синтетический добор до ~1600.
    """
    parquet = DATA_DIR / "stars_hyg.parquet"
    if parquet.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(parquet)
            return {
                "ra":  df["ra"].to_numpy(dtype=float),
                "dec": df["dec"].to_numpy(dtype=float),
                "mag": df["mag"].to_numpy(dtype=float),
            }
        except Exception:
            pass  # битый parquet → откатываемся на встроенный набор

    ra  = np.array([s[0] for s in _STARS.values()], dtype=float)
    dec = np.array([s[1] for s in _STARS.values()], dtype=float)
    mag = np.array([s[2] for s in _STARS.values()], dtype=float)

    # ── синтетический добор до ~1600 звёзд (детерминированный) ──
    n_filler = 1600 - len(ra)
    if n_filler > 0:
        rng = np.random.default_rng(seed=42)
        ra_f  = rng.uniform(0.0, 360.0, n_filler)
        # равномерное по сфере: uniform в sin(dec)
        dec_f = np.degrees(np.arcsin(rng.uniform(-1.0, 1.0, n_filler)))
        mag_f = rng.uniform(2.5, 5.0, n_filler)
        ra  = np.concatenate([ra,  ra_f])
        dec = np.concatenate([dec, dec_f])
        mag = np.concatenate([mag, mag_f])

    return {"ra": ra, "dec": dec, "mag": mag}


# ── Созвездия ───────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def load_constellations() -> dict:
    """
    Возвращает:
      segments: list[(ra1, dec1, ra2, dec2, name_ru)]
      centroids: dict[name_ru] = (ra, dec)
      all_names: list[str] всех 88
      major:    set[str] главных для подписи
    """
    segments: list[tuple[float, float, float, float, str]] = []
    centroids: dict[str, tuple[float, float]] = {}

    for cname, pairs in _CONSTELLATION_LINES.items():
        ras, decs = [], []
        for a, b in pairs:
            # Защита: если вдруг звезды нет в каталоге — пропускаем отрезок
            if a not in _STARS or b not in _STARS:
                continue

            ra_a,  dec_a,  _ = _STARS[a]
            ra_b,  dec_b,  _ = _STARS[b]
            segments.append((ra_a, dec_a, ra_b, dec_b, cname))
            ras.extend([ra_a, ra_b])
            decs.extend([dec_a, dec_b])

        if ras and decs:
            centroids[cname] = (float(np.mean(ras)), float(np.mean(decs)))

    return {
        "segments":  segments,
        "centroids": centroids,
        "all_names": list(ALL_CONSTELLATIONS),
        "major":     set(MAJOR_CONSTELLATIONS),
    }