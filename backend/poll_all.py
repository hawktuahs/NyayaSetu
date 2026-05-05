import httpx
import asyncio
import time

async def poll_all():
    print("Polling for all extractions...")
    while True:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                r = await client.get('http://localhost:8000/api/cases')
                cases = r.json()
                
                pending = [c for c in cases if c['status'] in ['extracting', 'pending_extraction']]
                verified = [c for c in cases if c['status'] == 'pending_verification']
                errors = [c for c in cases if c.get('extraction_error')]
                
                print(f"\rStatus: {len(pending)} pending, {len(verified)} verified, {len(errors)} with errors", end="")
                
                if not pending:
                    print("\nAll extractions finished!")
                    for c in verified:
                        print(f"Verified Case {c['id']}: {c['original_filename']} - {c['status']}")
                    for c in errors:
                        print(f"Error Case {c['id']}: {c['original_filename']} - {c['extraction_error'][:100]}")
                    break
            except Exception as e:
                print(f"\nPoll failed: {e}")
                
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(poll_all())
