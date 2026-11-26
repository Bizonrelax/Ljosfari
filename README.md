# QWR v1.0 — Autonomous Research Protocol

QWR is a subject-neutral protocol for autonomous scientific work by LLM agents. The subject is a *claim*, not code. The goal is discoveries, or positive progress toward discoveries, recorded so that a human can find and reuse them a month later after forgetting everything.

The protocol lives in `qwr/bot/` of the target repository (for example Ljosfari). Research results live in `fixrealm/` (or another repository via `QWR_FIXREALM`). The protocol is read-only for agents; editing it is a separate role (EDT) activated only by a human lever.

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

PLN planner (always one), WRK executor, EUR heuristic guess generator, CHK independent verifier (priority over WRK), LIT novelty scout. EDT protocol editor is human-lever-only. Role is not preassigned: an agent reads a state slice and claims a role atomically (create without sha: 201 yours, 422/409 busy). At most three agents at once.

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

## Safety

The token stays in an environment variable only. No force-push to main, no pushing red, no editing the protocol from an executor role, no deleting cards/traces/births, no renumbering, no status inflation, no passing "not found" off as a discovery, no task without a cost estimate, no loading foreign roles or whole dictionaries, no invented work.

---

# QWR v1.0 — протокол автономного исследования

QWR — предметно-нейтральный протокол автономной научной работы агентов. Предмет — утверждение, не код. Цель — открытия или положительный сдвиг к открытиям, зафиксированные так, что человек найдёт и переиспользует их через месяц, всё забыв.

Протокол лежит в папке `qwr/bot` целевого репозитория (например Ljosfari). Результаты — в `fixrealm/` (или другом репозитории через `QWR_FIXREALM`). Протокол агенту только чтение; правка — отдельная роль EDT по рычагу человека.

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

PLN планировщик (всегда один), WRK исполнитель, EUR эвристический генератор догадок, CHK независимый проверяющий (приоритет над WRK), LIT разведчик новизны. EDT редактор протокола — только по рычагу человека. Роль не назначается заранее: агент берёт срез состояния и захватывает роль атомарно (создание без sha: 201 твоё, 422/409 занято). Одновременно не более трёх агентов.

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

## Безопасность

Токен только в переменной окружения. Не force-push в main, не пуш красного, не правка протокола из роли исполнителя, не удаление карточек/следов/рождений, не перенумерация, не повышение статуса без основания, не выдавать «не найдено» за открытие, не брать задачу без оценки стоимости, не грузить чужие роли и словари целиком, не выдумывать работу.
