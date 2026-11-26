# QWR v1.0 — Autonomous Research Protocol

QWR is a subject-neutral protocol for autonomous scientific work by LLM agents. The subject is a *claim*, not code. The goal is discoveries, or positive progress toward discoveries, recorded so that a human can find and reuse them a month later after forgetting everything.

The protocol lives in `qwr/bot/` of the target repository (for example Ljosfari). The `fixrealm/` folder sits at the root of the same repository and accumulates all results produced by the bots. Bots write their results there themselves, through the protocol tools, using their own token; no human is needed for that. "Read-only for agents" applies to the protocol files in `qwr/bot/`, not to `fixrealm/`: bots write `fixrealm/` freely under their role permissions. Editing the protocol is a separate role (EDT) activated only by a human lever.

## Structure

- `README.md` — this file, English first, Russian below.
- `MANIFEST.json` — versions, hashes, token estimates per protocol file; checked at entry.
- `SELFTEST.md` — golden case and delivery checks.
- `qwr/GUIDE.md` — detailed human guide (Russian).
- `qwr/bot/GATE.txt` — the gate, single entry point.
- `qwr/bot/dict/` — dictionaries: common, group, role, subject.
- `qwr/bot/roles/` — one file per role: PLN, WRK, EUR, CHK, LIT, EDT.
- `qwr/bot/mod/` — needs and lazy modules.
- `qwr/bot/bin/qwr.py` — protocol tools (stdlib only).
- `qwr/bot/a2a/` — agent exchange: ledger, tasks, inbox, births, locks.
- `fixrealm/` — results: INDEX.tsv, INDEX.md, TERMS.md, JOURNAL.md, cards/, data/.

## Roles

PLN planner (always one), WRK executor, EUR heuristic guess generator (within an open question), CHK independent verifier (priority over WRK), LIT novelty scout. Plus IDE direction generator (chooses subject/direction only when the swarm is idle, seeds ≤3 checkable directions, hands off to PLN), SYN synthesizer (survey and connections when many cards accumulate), AUD registry auditor (hygiene, drift, defects to PLN). EDT protocol editor is human-lever-only; observer and cleanup are levers (ОБЗОР, РАСЧИСТИ). Role is not preassigned: an agent reads a state slice and claims a role atomically (create without sha: 201 yours, 422/409 busy). At most three agents at once.

## Two axes, never mixed

Truth: def, prf, emp, hyp, opn, ref. Novelty: cls, knw, nfd, unc. emp→prf only with a written proof plus a closed CHK task by another agent; prf→ref only with an explicit counterexample; knw needs a link; nfd needs two named sources with a check date, otherwise unc. nfd never means "new".

## Tangibility

Every task carries a cost estimate, memory estimate, stage ceiling, tangible artifact, acceptance criterion. Default ceiling 10^7 operations or 120 seconds, memory 512 MB, output 5 MB. A task above the ceiling is decomposed, never run. Three stages without a positive shift park the branch. Negative results are recorded equally.

## Budgets (token estimates)

gate ≤3000, role card ≤800, role file ≤2500, needs ≤6000, slice ≤1500, decode ≤500, session entry ≤18000 (target 12000). Over budget: narrow the slice, do not read more.

## Quick start

Launch message to an agent:

    Token: <your PAT>
    Repository: OWNER/REPO
    Protocol: QWR v1.0, folder qwr/bot. Read qwr/bot and execute.

A lever is a separate line starting with `РЫЧАГ`; only the lever is executed. Work goes straight to `main`, one green stage = one push. Never push red, never force-push main, never write the token to files or history.

Checks: `python3 qwr/bot/bin/qwr.py doctor` and `python3 qwr/bot/bin/qwr.py selftest`.

## Push discipline

Publishing is mandatory, not optional. When state is GREEN and verdict is PUBLISH, the stage is fixed in `fixrealm/`, the manifest matches, and quota/tools/calls are available, the bot must push itself to `main` (no branches, no force). Immediately after a successful push it STOPS: report and exit, no further research in the same message. The next research starts only in the next human message or a new chat. If quota or tooling for push is missing, the bot does not keep computing: it fixes the stage, leaves a pending trace, reports DO NOT PUBLISH with a reason, and exits. Red is never pushed. `qwr.py publish` enforces the condition; the lever `РЫЧАГ: ПУБЛИКУЙ` and a direct "publish" instruction trigger the same push-and-stop. `fixrealm/INDEX.md` has hyperlinks to cards and data: read, click, jump.

## Pre-publish gate

A mandatory cheap gate runs before a card is published, inline in the stage (not a separate task): any new formula/invariant/generalization is run against already-saved `data/*.tsv` rows via `qwr.py precheck`; a generalization transferred from a special case is rejected if it breaks on any saved solution, and the self-check is recorded in the card. `qwr.py lint` (and `publish`) enforce integrity: INDEX matches cards, links and data exist, 12 columns intact, no `%s` placeholders in human text, no duplicate bodies, single QWR version stamp. Results stay Markdown + TSV in the repo with generated INDEX; hand-carrying to Word/docx is forbidden because it makes `emp` unverifiable. Novelty is checked by LIT before big enumeration or range extension; extending a classic range without a new question is waste. Independent CHK by another agent for emp→prf is unchanged.

## Reuse: ladder and foundation

Cards are steps of a ladder and bricks of a foundation for every later bot. Reuse is mandatory: before new computation a bot reads prior results selectively (`qwr.py prior --query`, `qwr.py card-get --id`), uses proven `prf` claims as lemmas without recomputing, does not repeat `ref` dead-ends without a new angle, extends `emp` ranges from the saved boundary, reuses `latent` utility, and records prior card numbers in the links field so the ladder is traceable. PLN never issues tasks redoing proven or refuted claims without a new question.

## Safety

The token stays in an environment variable only. No force-push to main, no pushing red, no editing the protocol from an executor role, no deleting cards/traces/births, no renumbering, no status inflation, no passing "not found" off as a discovery, no task without a cost estimate, no loading foreign roles or whole dictionaries, no invented work.

---

# QWR v1.0 — протокол автономного исследования

QWR — предметно-нейтральный протокол автономной научной работы агентов. Предмет — утверждение, не код. Цель — открытия или положительный сдвиг к открытиям, зафиксированные так, что человек найдёт и переиспользует их через месяц, всё забыв.

Протокол лежит в папке `qwr/bot` целевого репозитория (например Ljosfari). Папка `fixrealm/` лежит в корне того же репозитория и накапливает все результаты работы ботов. Боты вносят результаты туда сами, через инструменты протокола, со своим токеном; человек для этого не нужен. «Только чтение» относится к файлам протокола `qwr/bot/`, а не к `fixrealm/`: в `fixrealm/` боты пишут свободно по правам своей роли. Правка протокола — отдельная роль EDT по рычагу человека.

## Структура

- `README.md` — этот файл, английский выше, русский ниже.
- `MANIFEST.json` — версии, хэши, оценки токенов по файлам протокола; проверка при входе.
- `SELFTEST.md` — золотой случай и проверки поставки.
- `qwr/GUIDE.md` — подробное руководство для человека.
- `qwr/bot/GATE.txt` — шлюз, единственная точка входа.
- `qwr/bot/dict/` — словари: общий, групповой, ролевой, предметный.
- `qwr/bot/roles/` — по файлу на роль: PLN, WRK, EUR, CHK, LIT, EDT.
- `qwr/bot/mod/` — модули needs и lazy.
- `qwr/bot/bin/qwr.py` — инструменты протокола (только stdlib).
- `qwr/bot/a2a/` — обменники агентов: реестр, задачи, inbox, рождения, замки.
- `fixrealm/` — результаты: INDEX.tsv, INDEX.md, TERMS.md, JOURNAL.md, cards/, data/.

## Роли

PLN планировщик (всегда один), WRK исполнитель, EUR эвристический генератор догадок (внутри открытого вопроса), CHK независимый проверяющий (приоритет над WRK), LIT разведчик новизны. Плюс IDE генератор направлений (выбирает предмет/направление только при простое роя, посев ≤3 проверяемых направлений, ход передаёт PLN), SYN синтезатор (обзор и связи при накоплении карточек), AUD аудитор реестра (гигиена, дрейф, дефекты PLN). EDT редактор протокола — только по рычагу человека; наблюдатель и расчистка — рычаги ОБЗОР и РАСЧИСТИ. Роль не назначается заранее: агент берёт срез состояния и захватывает роль атомарно (создание без sha: 201 твоё, 422/409 занято). Одновременно не более трёх агентов.

## Две оси, никогда не смешивать

Истина: def, prf, emp, hyp, opn, ref. Новизна: cls, knw, nfd, unc. emp→prf только письменным доказательством плюс закрытая задача CHK другим агентом; prf→ref только явным контрпримером; knw требует ссылки; nfd требует двух названных источников с датой проверки, иначе unc. nfd не означает «ново».

## Осязаемость

Каждая задача несёт оценку стоимости, память, потолок этапа, осязаемый артефакт, критерий приёмки. Потолок по умолчанию 10^7 операций или 120 секунд, память 512 МБ, выгрузка 5 МБ. Задача выше потолка декомпозируется, а не выполняется. Три этапа без сдвига замораживают ветку. Отрицательный результат фиксируется наравне с положительным.

## Бюджеты (оценка токенов)

шлюз ≤3000, карточка роли ≤800, ролевой файл ≤2500, needs ≤6000, срез ≤1500, расшифровка ≤500, вход сессии ≤18000 (цель 12000). Превысил — сужай срез, а не дочитывай.

## Запуск

Сообщение запуска агенту:

    Токен: <ваш PAT>
    Репозиторий: OWNER/REPO
    Протокол: QWR v1.0, папка qwr/bot. Читай qwr/bot и выполняй.

Рычаг — отдельная строка со слова `РЫЧАГ`; исполняется только он. Работа прямо в `main`, один зелёный этап — один пуш. Не пушить красное, не force-push в main, не писать токен в файлы и историю.

Проверки: `python3 qwr/bot/bin/qwr.py doctor` и `python3 qwr/bot/bin/qwr.py selftest`.

## Дисциплина пуша

Публикация обязательна, а не по желанию. Если СОСТОЯНИЕ ЗЕЛЕНО и ВЕРДИКТ ПУБЛИКОВАТЬ, этап зафиксирован в `fixrealm/`, манифест сошёлся и есть квоты, инструменты и вызовы — бот обязан запушить сам в `main`, без веток и force. Сразу после успешного пуша — СТОП: отчёт и выход, без новых исследований в том же сообщении. Следующее исследование — только в следующем сообщении человека или новом чате. Нет квоты или инструмента на пуш — бот не считает дальше: фиксирует этап, оставляет pending, отчёт НЕ ПУБЛИКОВАТЬ с причиной, выход. Красное не пушится. `qwr.py publish` проверяет условие; рычаг `РЫЧАГ: ПУБЛИКУЙ` и прямое «публикуй» запускают тот же пуш-и-стоп. `fixrealm/INDEX.md` содержит гиперссылки на карточки и данные: прочёл, тыкнул, перелетел.

## Гейт перед публикацией

Обязательный дешёвый гейт до публикации карточки, встроенный в этап: любая новая формула, инвариант или обобщение прогоняется на сохранённых строках `data/*.tsv` через `qwr.py precheck`; обобщение с частного случая отклоняется, если ломается на сохранённом решении, самопроверка записывается в карточку. `qwr.py lint` и `publish` проверяют целостность: INDEX сходится с карточками, ссылки и data существуют, 12 колонок целы, плейсхолдеров `%s` в тексте нет, дублей нет, штамп версии един (QWR). Результаты — Markdown и TSV в репозитории, INDEX генерируется; ручной перенос в Word/docx запрещён, он делает emp непроверяемым. Новизну закрывает LIT до большого перебора; расширение диапазона классики без нового вопроса — работа впустую. Независимая проверка CHK другим агентом для emp→prf сохраняется.

## Повторное использование: лестница и фундамент

Карточки — ступеньки лестницы и кирпичики фундамента для всех следующих ботов. Повторное использование обязательно: перед новым счётом бот выборочно читает прежние результаты (`qwr.py prior --query`, `qwr.py card-get --id`), использует доказанное `prf` как леммы без пересчёта, не повторяет тупики `ref` без нового угла, расширяет диапазоны `emp` от сохранённой границы, переиспользует `latent` пользу и указывает номера прежних карточек в поле связей, чтобы лестница прослеживалась. PLN не выдаёт задач на уже доказанное или опровергнутое без нового вопроса.

## Безопасность

Токен только в переменной окружения. Не force-push в main, не пуш красного, не правка протокола из роли исполнителя, не удаление карточек/следов/рождений, не перенумерация, не повышение статуса без основания, не выдавать «не найдено» за открытие, не брать задачу без оценки стоимости, не грузить чужие роли и словари целиком, не выдумывать работу.
