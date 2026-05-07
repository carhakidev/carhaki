import anthropic
from django.conf import settings
from apps.core.models import APILog


def generate_ai_summary(processed_data: dict) -> str:
    if not settings.ANTHROPIC_API_KEY:
        return ''

    vehicle = processed_data.get('vehicle', {})
    brands = processed_data.get('brands', [])
    accidents = processed_data.get('accidents', [])
    recalls = [r for r in processed_data.get('recalls', []) if r.get('is_open')]
    theft = processed_data.get('theft', [])
    total_loss = processed_data.get('total_loss', False)
    odometer_records = processed_data.get('odometer_records', [])
    auction_grade = processed_data.get('auction_grade')
    shaken_expiry = processed_data.get('shaken_expiry')
    uganda = processed_data.get('uganda_eligibility', {})
    source = processed_data.get('meta', {}).get('source_country', 'USA')

    prompt = f"""You are a vehicle history expert writing a clear, simple summary for a Ugandan car buyer who may not be familiar with technical automotive terms.

Vehicle: {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')} {vehicle.get('trim', '')}
Source Country: {source}
Title Brands/Issues: {', '.join(brands) if brands else 'None'}
Accidents: {len(accidents)} recorded ({sum(1 for a in accidents if a.get('airbags_deployed')) } with airbags deployed)
Total Loss: {'YES' if total_loss else 'No'}
Theft Records: {len(theft)}
Open Recalls: {len(recalls)} open recall(s)
Odometer Records: {len(odometer_records)} readings recorded
{"Auction Grade (Japan): " + str(auction_grade) if auction_grade else ""}
{"Shaken (MOT) Expiry: " + str(shaken_expiry) if shaken_expiry else ""}
Uganda Import Eligible: {'Yes' if uganda.get('eligible') else 'NO - ' + uganda.get('note', '')}

Write a 3-4 sentence plain English summary. Be direct about risks. End with a recommendation (recommend physical inspection for all vehicles). Use simple language — no jargon. Do not start with "I" or "This vehicle". Start with the vehicle name."""

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    import time
    start = time.time()
    try:
        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=300,
            messages=[{'role': 'user', 'content': prompt}]
        )
        elapsed = int((time.time() - start) * 1000)
        summary = message.content[0].text.strip()

        APILog.objects.create(
            provider=APILog.ANTHROPIC,
            endpoint='messages',
            identifier=processed_data.get('meta', {}).get('identifier', ''),
            cost_usd=0.0003,
            success=True,
            response_time_ms=elapsed,
        )
        return summary
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        APILog.objects.create(
            provider=APILog.ANTHROPIC,
            endpoint='messages',
            identifier=processed_data.get('meta', {}).get('identifier', ''),
            cost_usd=0,
            success=False,
            response_time_ms=elapsed,
            error_message=str(e),
        )
        return ''
