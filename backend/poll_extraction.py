import httpx
import asyncio

async def poll():
    for i in range(40):
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get('http://localhost:8000/api/cases/1')
            d = r.json()
            status = d['status']
            err = (d.get('extraction_error') or '').strip()
            print(f'[{i*10}s] {status}' + (f' | {err[:80]}' if err else ''))
            if status == 'pending_verification':
                e = d.get('extraction') or {}
                p = d.get('action_plan') or {}
                print()
                print('CASE:', e.get('case_number'))
                print('COURT:', e.get('court'))
                print('DATE:', e.get('date_of_order'))
                print('OUTCOME:', e.get('outcome'))
                print('GOVT_OUTCOME:', e.get('outcome_for_government'))
                print('GOVT_PARTY:', e.get('government_party'))
                print('STAY:', e.get('stay_status'))
                print()
                print('ACTION_TYPE:', p.get('action_type'))
                print('PRIORITY:', p.get('priority'))
                print('URGENCY:', p.get('urgency_reason'))
                flags = p.get('critical_flags') or []
                print('FLAGS:', len(flags), [f.get('flag') for f in flags])
                actions = p.get('immediate_actions') or []
                print('ACTIONS:', len(actions), [a.get('action', '')[:60] for a in actions])
                break
        await asyncio.sleep(10)

asyncio.run(poll())
