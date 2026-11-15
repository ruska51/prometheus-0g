"""Glossary of the terms used on the dashboard, in English and Russian (ADR-055).

Definitions only restate what the pages and docs/PHYSICS.md already use; no new numbers.
"""

from __future__ import annotations

import streamlit as st
from i18n import lang, t

# term -> (English definition, Russian term, Russian definition)
TERMS: list[tuple[str, str, str, str]] = [
    (
        "Burning-rate constant K",
        "How fast a droplet burns: the slope of the droplet diameter squared against time, in mm²/s. Higher K = faster.",
        "Константа скорости горения K",
        "Насколько быстро горит капля: наклон квадрата диаметра капли по времени, мм²/с. Больше K - быстрее.",
    ),
    (
        "d²-law",
        "For a steadily burning droplet the square of its diameter falls linearly with time: d² = d0² - K t. So a droplet "
        "of diameter d0 burns out in d0²/K.",
        "Закон d²",
        "У равномерно горящей капли квадрат диаметра убывает линейно: d² = d0² - K t. Капля диаметром d0 сгорает за d0²/K.",
    ),
    (
        "Microgravity",
        "Near-weightlessness, as on the ISS. Hot gas does not rise, so a flame has no plume: it is a slow, sphere-like "
        "flame fed only by diffusion.",
        "Невесомость (микрогравитация)",
        "Почти полное отсутствие веса, как на МКС. Горячий газ не всплывает, у пламени нет факела: оно медленное, почти "
        "сферическое и питается только диффузией.",
    ),
    (
        "Lunar gravity (1/6 g)",
        "Gravity on the Moon's surface, one sixth of Earth's. Weak buoyancy still feeds a flame.",
        "Лунная гравитация (1/6 g)",
        "Сила тяжести на поверхности Луны, шестая часть земной. Слабая плавучесть всё равно подпитывает пламя.",
    ),
    (
        "Moon-base atmosphere",
        "The planned air of Moon bases and pressurized rovers from the challenge page: 30 % oxygen or more at 10.2 psi or "
        "less. ISS air is 21 % oxygen at 14.7 psi.",
        "Атмосфера лунной базы",
        "Планируемый воздух лунных баз и герметичных роверов со страницы челленджа: 30 % кислорода и больше при 10.2 psi "
        "и меньше. Воздух МКС - 21 % кислорода при 14.7 psi.",
    ),
    (
        "Self-extinction",
        "The flame goes out by itself before the fuel is used up.",
        "Самозатухание",
        "Пламя гаснет само, не дожигая топливо.",
    ),
    (
        "Flame temperature",
        "Adiabatic flame temperature from chemical equilibrium with dissociation (Cantera with NASA thermodynamic data).",
        "Температура пламени",
        "Адиабатическая температура пламени из химического равновесия с диссоциацией (Cantera с термодинамикой NASA).",
    ),
    (
        "psi, atm",
        "Pressure units: 1 atm = 14.696 psi (pounds per square inch).",
        "psi, атм",
        "Единицы давления: 1 атм = 14.696 psi (фунтов на квадратный дюйм).",
    ),
    (
        "Mole fraction",
        "Share of a gas in a mixture by number of molecules: oxygen 0.30 = 30 % O2.",
        "Мольная доля",
        "Доля газа в смеси по числу молекул: кислород 0.30 = 30 % O2.",
    ),
    (
        "PSI",
        "NASA Physical Sciences Informatics: the public repository of ISS physical-science experiments and their data "
        "(psi.nasa.gov).",
        "PSI",
        "NASA Physical Sciences Informatics: открытый архив физических экспериментов МКС и их данных (psi.nasa.gov).",
    ),
    (
        "FLEX, BASS-II, ACME CFI-G, SAME-R",
        "NASA ISS combustion experiments used here: burning droplets (FLEX), burning solids (BASS-II), gas flames (ACME "
        "CFI-G), smoke particles (SAME-R).",
        "FLEX, BASS-II, ACME CFI-G, SAME-R",
        "Эксперименты NASA по горению на МКС, которые мы используем: горящие капли (FLEX), горящие твёрдые материалы "
        "(BASS-II), газовые пламена (ACME CFI-G), частицы дыма (SAME-R).",
    ),
    (
        "Saffire, LUCI",
        "Saffire: large fire tests on uncrewed cargo spacecraft after leaving the ISS. LUCI: burning materials at lunar "
        "gravity on a sounding rocket. Their flame-spread rates drive the Module fire page.",
        "Saffire, LUCI",
        "Saffire: большие огневые испытания на беспилотных грузовых кораблях после ухода с МКС. LUCI: горение материалов "
        "при лунной гравитации на суборбитальной ракете. Их скорости распространения пламени используются на странице "
        "«Пожар в модуле».",
    ),
    (
        "Hybrid model",
        "Our model: classic droplet-burning physics, a per-fuel factor, and machine learning that learns only what the "
        "physics misses.",
        "Гибридная модель",
        "Наша модель: классическая физика горения капли, поправка на топливо и машинное обучение, которое учит только то, "
        "что физика не объясняет.",
    ),
    (
        "95 % band",
        "The range in which the model expects the true value with 95 % probability.",
        "Полоса 95 %",
        "Диапазон, в котором модель ожидает истинное значение с вероятностью 95 %.",
    ),
    (
        "In range / extrapolation",
        "In range: close to conditions NASA tested. Extrapolation: outside them - the number is a model estimate, trust it less.",
        "В диапазоне / экстраполяция",
        "В диапазоне: близко к условиям испытаний NASA. Экстраполяция: за их пределами - число является оценкой модели, "
        "доверять ему меньше.",
    ),
    (
        "Grouped cross-validation",
        "Testing a model on data it did not see, where repeats of the same test regime always stay together, so the "
        "model cannot memorise them.",
        "Групповая кросс-валидация",
        "Проверка модели на данных, которых она не видела, причём повторы одного режима испытаний всегда остаются вместе, "
        "чтобы модель не могла их запомнить.",
    ),
    (
        "Flame-spread rate",
        "How fast the flame front moves over a solid material, in mm/s.",
        "Скорость распространения пламени",
        "Скорость, с которой фронт пламени движется по твёрдому материалу, мм/с.",
    ),
    (
        "Zone model",
        "A compartment-fire model that treats the module air as one well-mixed volume: the fire uses oxygen, adds CO2 and heat.",
        "Зонная модель",
        "Модель пожара в помещении, где воздух модуля - один хорошо перемешанный объём: пожар расходует кислород, "
        "добавляет CO2 и тепло.",
    ),
    (
        "Firebreak",
        "A strip of non-flammable material (here 50 cm of metal) placed to stop the flame on its way to the hatch.",
        "Противопожарная преграда",
        "Полоса негорючего материала (здесь 50 см металла), которая останавливает пламя на пути к люку.",
    ),
    (
        "Evidence types",
        "NASA data: measured in NASA tests. Model: our prediction. Physics theory: textbook equations. NASA literature: "
        "quoted from NASA reports. NASA history / spinoff: past accidents and technologies, no numbers.",
        "Типы доказательств",
        "Данные NASA: измерено в испытаниях NASA. Модель: наш прогноз. Физическая теория: уравнения из учебников. "
        "Литература NASA: цитаты из отчётов NASA. История / спинофф NASA: прошлые аварии и технологии, без чисел.",
    ),
]


def entries() -> list[tuple[str, str]]:
    ru = lang() == "ru"
    return [(r_term if ru else term, r_def if ru else en_def) for term, en_def, r_term, r_def in TERMS]


def sidebar_glossary() -> None:
    """A searchable glossary in a sidebar popover, on every page."""
    with st.sidebar.popover(t("Glossary"), icon=":material/menu_book:", use_container_width=True):
        q = st.text_input(t("Find a term"), key="glossary_q", placeholder="K, PSI, ...").strip().lower()
        for term, d in entries():
            if not q or q in term.lower() or q in d.lower():
                st.markdown(f"**{term}** - {d}")


def glossary_section() -> None:
    st.subheader(t("Glossary"))
    st.markdown("\n".join(f"- **{term}** - {d}" for term, d in entries()))
