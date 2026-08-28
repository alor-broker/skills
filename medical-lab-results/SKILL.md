---
name: medical-lab-results
description: "Explain laboratory results from exact values, units, report intervals, context, and trends without generic ranges or isolated diagnosis. / Объяснять анализы по точным значениям, единицам, интервалам отчёта, контексту и динамике без универсальных норм и диагноза по одному показателю."
---

# Medical Laboratory Results

Explain what a laboratory report can and cannot show. Treat the reporting laboratory’s data as authoritative for the measurement details, not as a complete diagnosis.

## Safety gate

If the report marks a result as critical, the laboratory or clinician has already asked for urgent contact, or the user has serious symptoms, lead with the appropriate urgent action. A potentially critical result is not a literature-search task. Do not invent a universal critical threshold.

## Verify the input

For every interpreted result, obtain or visibly mark as missing:

- exact test and analyte name;
- value, unit, and laboratory-provided reference interval;
- high, low, critical, hemolysis, lipemia, or other report flags;
- specimen type and collection date/time;
- age or age range and relevant sex, pregnancy, or postpartum context;
- fasting/preparation status and recent exercise when relevant;
- symptoms, relevant conditions, medicines, and supplements;
- prior values with dates, preferably from the same laboratory and method.

When values come from an image or optical character recognition, label the table “unconfirmed transcription,” then ask the user to confirm the numbers, decimal separators, signs, units, and flags before consequential interpretation. Never describe this first-pass table as verified.

If the original report visibly marks a result critical or the user has serious symptoms, possible recognition uncertainty must not delay contact with the laboratory, clinician, or emergency service. Tell the user to act from the original report and professional instructions while the transcription is checked.

## Interpretation rules

- Say “reference interval,” not “normal range.”
- Use the interval printed on the report. Do not silently replace it with an internet range.
- Never compare or convert values until the unit and conversion are explicit and verified.
- Distinguish a reference interval from a clinical decision limit, treatment target, or critical-risk threshold.
- Explain that an out-of-range result may not mean disease and an in-range result may not exclude disease.
- Interpret related analytes together and in clinical context; do not diagnose from an isolated number.
- Describe trends only with dates, units, method/laboratory comparability, and likely biological or analytical variation.
- Consider preparation, collection, transport, assay interference, medicines, acute illness, and other pre-analytical or analytical factors when relevant.
- Do not apply adult intervals to children, pregnancy-specific questions, or other populations without an applicable source.

If the report’s interval or unit is missing, explain only the test’s general purpose and ask for the missing report details. Specialized pathology, cytology, genetics, blood-gas, microbiology-susceptibility, and similar reports require the appropriate clinician or laboratory specialist.

## Output

Provide:

1. a transcription marked confirmed or unconfirmed;
2. what each result measures, in plain language;
3. how the result compares with the report’s own interval or decision limit;
4. plausible categories of explanation, without selecting a diagnosis;
5. important context and missing data;
6. what to discuss with the ordering clinician and how soon;
7. any report-defined or symptom-driven urgent action first.

Do not recommend starting, stopping, or changing treatment solely from the laboratory result.

## Privacy and sources

Ask the user to remove identifiers, barcodes, QR codes, and unnecessary exact dates from uploaded reports. Do not persist results without explicit consent.

Useful authoritative anchors:

- NIH MedlinePlus on report-specific reference intervals: `https://medlineplus.gov/lab-tests/how-to-understand-your-lab-results/`
- CLSI EP28 on establishing and verifying reference intervals: `https://clsi.org/shop/standards/ep28/`
- CLSI GP47 on critical-risk results: `https://clsi.org/shop/standards/gp47/`
