#!/usr/bin/env python3
"""Write index/status.csv: one row per plan project with its implementation status.

The MATCH list below is the hand-made record of which council matters and parish report lines
belong to which plan row. It is the only place that evidence is entered: add or change a rule
here, run this script, then run status_ledger_md.py. Edits made directly to status.csv or to
references/status-ledger.md are overwritten on the next run.
"""
import csv, sys, collections
from pathlib import Path
SK=Path(__file__).resolve().parents[1]
AS_OF='2026-10-13'
M={r['matter_file']:r for r in csv.DictReader(open(SK/'index/legistar_matters.csv'))}
def src(files):
    if not files: return 'Parish capital projects report, 2026-07-31'
    out=[]
    for f in files:
        r=M[f]; kind='Res.' if r['type']=='Resolution' else 'Ord.'
        en=r['enactment_no'] or 'not enacted ('+r['status']+')'
        out.append(f"{kind} {en} [file {f}, {r['passed_date'] or r['intro_date']}]")
    return '; '.join(out)
def last(files): return '2026-07-31' if not files else max((M[f]['passed_date'] or M[f]['intro_date']) for f in files)
D='Design or survey contract only; no construction contract found.'
# (doc prefix, project id, name substring) -> status, built scope, matters, note, independent source, its date
MATCH=[
('ormond','2-1','CN RR Jack','Under construction','Parish news: three 60-inch and two 54-inch jack-and-bore culverts at two locations',
 ['2020-0258','2023-0170','2025-0184','2025-0393','2026-0253'],
 'Ormond CN Railway Culverts (P200801). Contract $10,542,425.00 (BLD Services); Change Order 1 adds $1,005,921.76. State CDBG-MIT agreement $6,314,616.00.',
 'stcharlesparish.gov news: groundbreaking 2025-12-09; first of five bores set for 2026-08-26 (https://www.stcharlesparish.gov/Home/Components/News/News/15862/26)','2026-08-24'),
('ormond','1-1','Destrehan #2 Sump','Built','Match to this plan row unconfirmed. Bid tabulations show 8,868 CY of excavation, 27,568 SF of steel sheet pile wall, a trash rack structure and 12 bar screen cleaners (P181101), and 15,930 SF of sheet piling with 1,232 CY of excavation (P190507). The plan row is a sump storage increase from 3,900 to 6,700 CUYD; neither document states a storage volume',
 ['2023-0141','2024-0119','2024-0320','2025-0026','2022-0338','2024-0202'],
 'Probable match. Two council projects at this station: Destrehan P.S. No. 2 Conveyance Improvements (P181101), contract $9,190,697.00, Change Order 3 (Final) 2025; and Hydraulic Bottleneck Near Destrehan P.S. No. 2 (P190507), contract $2,264,960.00, Change Order 2 (Final) 2024. Certificates of Substantial Completion: P181101 on 2024-10-21 (issued 2024-10-28), P190507 on 2024-04-03 (issued 2024-04-10). P181101 bid was a $7,426,997.00 base bid plus $1,763,700.00 Alternate 1. The two contracts total $11,455,657.00 before change orders against a plan cost of $3,300,000.',
 'stcharlesparish.gov news calls it "the recently improved Destrehan No. 2 Pump Station" (https://www.stcharlesparish.gov/Home/Components/News/News/15609/26)','2025-12'),
('ormond','1-5','Hill Heights','Built','Part only. The contract was for about 182 running feet of steel sheet piles to about 30 feet depth (5,511.6 SF installed); the plan row is about 690 linear feet. The parish report calls the finished work an emergency repair; Phase 2 ($3,150,000, design, bid in 2027 if funded) and Phase 3 ($1,500,000, on hold) remain unfunded',['2022-0068','2023-0152'],
 'Probable match. Hill Heights Drainage Improvements - Destrehan (P190802): contract with APC Construction, LLC dated 2023-02-13 for $844,383.00; Change Order 1 (Final) brought it to $728,098.20. Substantial completion 2023-05-08; final acceptance 2023-06-15. The contract is an attachment to files 2022-0068 and 2023-0152; no separate award ordinance was found by title. Final cost is against a plan cost of $4,973,750 for the full length.','',''),
('ormond','1-2','Dunleith Canal','Funded','',['2020-0232','2025-0027'],D+' Carriage/Dunleith Canals Drainage Structure (P200706), contract value now not to exceed $473,378.00. Council title describes a drainage structure; plan row is sheet piles.','',''),
('ormond','1-3','Carriage Lane','Funded','',['2020-0231','2020-0232','2020-0234'],D+' Carriage Canal Widening (P200705); Carriage/Dunleith structure (P200706); Drainage Structure for Carriage, Houmas and A Canals (P200707). Titles describe widening and structures; plan row is sheet piles.','',''),
('ormond','1-4','Carriage Lane','Funded','',['2020-0231','2020-0232','2020-0234'],D+' Same council projects as Ormond 1-3.','',''),
('ormond','1-6','Canal A','Funded','',['2020-0233','2020-0234'],D+' Canal A Improvements (P200704); Drainage Structure for Carriage, Houmas and A Canals (P200707).','',''),
('ormond','1-7','Houma','Funded','',['2020-0234'],D+' Drainage Structure for Carriage, Houmas and A Canals (P200707).','',''),
('ormond','1-8','Ormond Oak','Funded','',['2022-0337','2023-0289'],D+' Ormond Oaks Channel (P210203), not to exceed $29,900.00; a 2023 amendment to $67,403.00 shows no enactment number.','',''),
('montz','1-1','200 CFS Pump Station','Under construction','267 cfs per the parish report (bid tabulation: four 67 CFS pumps), against 200 CFS in the plan row',
 ['2021-0097','2023-0169','2025-0107','2025-0339'],
 'Montz Pump Station No. 1 (P210301, CPRA PO-0200). Contract $13,479,955.00 (Sealevel); Change Order 1 adds $111,702.07. The parish report of 2026-07-31 calls this station "Montz Pump Station (at CN Railroad)"; the plan row puts its station on the CC Canal downstream of the railroad. The match rests on that location and is not confirmed from plans.',
 'Herald Guide, 2026-01: Montz 1 scheduled for completion end of 2026 (https://www.heraldguide.com/featured/185011)','2026-01'),
('montz','3-1','Additional Pump Station','Under construction','340 cfs per the parish report (bid tabulation: five 67 CFS pumps, which is 335), against 340 CFS in the plan row',
 ['2021-0267','2025-0188','2025-0193'],
 'Montz Pump Station No. 2 and Drainage Improvements (P210806). Contract $18,882,865.00 (Sealevel); the bid included the US 61 canal improvements (P230602). The parish report of 2026-07-31 calls it "Montz Pump Station #2 (at Airline)" and says the Corps permit requires removal of the Prescott Pump Station after startup, which matches the plan row (340 CFS station between the KCS railroad and Airline Highway, existing station removed).',
 'Herald Guide, 2026-01: Montz II scheduled for completion early 2027 (https://www.heraldguide.com/featured/185011)','2026-01'),
('montz','1-5','Jack-and-Bore at CN Railroad and Evangelin','Funded','',['2020-0344','2021-0214','2025-0200'],D+' Montz Railroad Culverts and Drainage Improvements (P201101); Evangeline Road & CN Railroad Box Culvert (P210701), contract value now $389,718.34.','',''),
('montz','1-6','Jack-and-Bore at CN Railroad and Hollywood','Funded','',['2020-0344'],D+' Montz Railroad Culverts and Drainage Improvements (P201101). The title does not name the crossing.','',''),
('montz','3-2','Concrete Box Culvert Under Evangeline','Funded','',['2021-0214','2025-0200'],D+' Evangeline Road & CN Railroad Box Culvert (P210701). The same council project is listed against Montz 1-5; the title does not say which plan row it is.','',''),
('norco','1-1','','Funded','',['2022-0173','2023-0162','2023-0343','2024-0049','2024-0354','2026-0265'],
 'Engineers Canal Pump Station Improvements (P220206): planning, design (not to exceed $716,508.00), Construction Manager at Risk pre-construction agreement $2,550,000.00 (Cajun Industries), state allocation $150,000.00, design refinement (P260803) not to exceed $1,423,978.00, and purchase of 679 West Pine Street. No construction contract found. Titles do not say which of the plan\'s two alternatives for 1-1 is being designed.','',''),
('new-sarpy','1-1','Schexnaydre Pump Station','Funded','',['2022-0174','2020-0228','2021-0224'],
 'Schexnaydre Pump Station Improvements (P220207): engineering $20,500.00 (2022), no construction contract found. An earlier project at the same station (P190502, contract $654,016.00) closed with a final change order in 2021-10; whether the plan row is that work or a further upgrade is not established.','',''),
('new-sarpy','1-2','New Sarpy Pump Station','Funded','',['2022-0172','2024-0248'],D+' New Sarpy Pump Station Improvements (P220203), amended to not to exceed $471,762.50.','',''),
('new-sarpy','2-','under CN RR','Funded','',['2025-0081'],D+' New Sarpy CN Culvert Crossings (P250301), not to exceed $692,052.00. The title does not say which crossings.','',''),
('st-rose','1-2','Oak St Pump Station','Funded','',['2025-0138'],D+' Oak Street Pump Station Improvements (P241104), $89,500.00. The corpus town hall deck (p13) lists a Louisiana Watershed Initiative application for Oak Street; no award found.','',''),
('almedia','1-2','Fairfield','Funded','',['2022-0083','2025-0215','2025-0218','2025-0318','2025-0324','2026-0244'],
 'State capital outlay agreement for Fairfield and Oakland Pump Station Discharge Improvements (FP&C 50-J45-21-02); Louisiana Watershed Initiative scope and budget revision (2025); Fairfield and Oakland Drainage Improvements (P251001) engineering not to exceed $787,285.30; grant applications to EDA (2025) and Delta Regional Authority ($500,000.00, 2026). No construction contract found. Titles say "discharge" and "conveyance" improvements, not station replacement.',
 'Corpus: st-rose-drainage-townhall-11123.md p13, $825,000 capital outlay marked awarded as of 2023-11-01. State Round 2 list: Fairfield and Oakland Pump Station Upgrades, $5.77 million, conditional on a feasibility study and full application (https://watershed.la.gov/round-2)','2026-10-13'),
('almedia','1-3','Oakland Pump Station','Funded','',['2022-0083','2025-0215','2025-0218','2025-0318','2025-0324','2026-0244'],'Same council record as Almedia 1-2.','Corpus: st-rose-drainage-townhall-11123.md p13','2023-11-01'),
('turtle-pond','2-1','Turtle Pond Pump Station','Funded','',['2025-0271','2025-0292','2025-0323','2026-0035','2026-0174'],
 D+' Turtle Pond Pump Station and Upstream Drainage Improvements (P250901), engineering not to exceed $609,085.50; Louisiana Watershed Initiative scope and budget revision (2025); Local Government Assistance Program application (2026). The 2027 proposed budget carries $15,000,000 for "LWI - Round 2 Turtle Pond Pump Station" in fund 313 and $4,342,441 in fund 112.','State Round 2 list: Turtle Pond Pump Station Upgrades, $9.23 million, conditional on a feasibility study and full application (https://watershed.la.gov/round-2)','2026-10-13'),
('hahnville-i','IG-1','King','Funded','',['2022-0057','2023-0287','2025-0232'],D+' King and Hahn Street Drainage Improvements (P220202): engineering not to exceed $432,650.00, plus amendments of $149,707.00 and $52,767.00.','',''),
('hahnville-i','IG-2','Hahn','Funded','',['2022-0057','2023-0287','2025-0232'],'Same council project as Hahnville 1 IG-1.','',''),
('hahnville-ii','IG-1','Bamboo','Funded','',['2023-0100'],'Survey contract only: Bamboo Street Drainage Improvements (P221101), $26,350.00. No design or construction contract found.','',''),
('amasellers','IG-1','Primary','Funded','',['2022-0171'],D+' U.P. Railroad Drainage Ditch and Outfall Improvements (P220205). The parish report calls it Priority 1 from the Ama watershed without naming the improvement group, so it is listed against both Priority 1 groups.','',''),
('amasellers','IG-2','Secondary','Funded','',['2022-0171'],'Same council project as Ama-Sellers IG-1.','',''),
('norco','1-3','','Funded','',['2022-0188'],D+' Clayton\'s Pond Outfall Improvements (P220204), which the parish report ties to Priority 3 and 4 of Norco Phase 1 and says the parish plans to cancel with the consultant. The report also lists an unfunded Engineers Canal Crossing at CPKC Railroad (three 72-inch culverts, status Negotiations), which matches this row\'s scope.','',''),
('norco','1-4','','Funded','',['2022-0188'],'Same council project as Norco 1-3 (Clayton\'s Pond Outfall Improvements, P220204).','',''),
('dianne-place','1-1','Dianne Place Pump Station','Funded','',[],'No council matter found by title. The parish report lists Dianne Pump Station (P241105), engineering agreement 12/19/2024, status Conceptual; preliminary report received 6/12/2025.','',''),
('mimosa-willowdale','','Willowdale Pump Station','Funded','',['2026-0328'],
 D+' Willowdale Pump Station Sump Improvements (P241102): Amendment No. 2 (not to exceed $315,610.00, overall $351,560.00) was at public hearing as of this ledger; the original agreement was not found by title search. The plan prints this row\'s cost as TBD.','',''),
]
TR=collections.defaultdict(list)
for t in csv.DictReader(open(SK/'index/parish_tracker_2026-07.csv')):
    for pr in t['plan_rows'].split('; '):
        if pr: TR[pr].append(f"{t['project']} ({t['project_no']}): {t['status']}, est. construction {t['est_construction_cost']}, {t['est_start']} to {t['est_end']}. {t['remarks']}" + (f" July: {t['july_note']}" if t['july_note'] else '') + (f" Report says: {t['plan_reference_in_report']}." if t['plan_reference_in_report'] else ''))
rows=[r for r in csv.DictReader(open(SK/'index/projects.csv')) if r['row_kind']=='project']
skip=[r for r in rows if 'townhall' in r['doc'] or 'public-meeting' in r['doc']]
rows=[r for r in rows if r not in skip]
used=collections.Counter(); out=[]; seenk=collections.Counter()
for r in rows:
    d=r['doc'].replace('-executive-summary','')
    hit=None
    for i,m in enumerate(MATCH):
        if d==m[0] and (r['project_id'].startswith(m[1]) if m[1].endswith('-') else r['project_id']==m[1]) and m[2].lower() in r['name'].lower():
            hit=m; used[i]+=1; break
    cost=r['cost'] or '/'.join(x for x in (r['cost_25yr'],r['cost_100yr']) if x)
    kk=(r['doc'],r['page'],r['table'],r['project_id']); seenk[kk]+=1
    base=dict(doc=r['doc'],page=r['page'],table=r['table'],project_id=r['project_id'],row=seenk[kk],name=r['name'],plan_cost=cost,as_of=AS_OF)
    lab=d+' '+(r['project_id'] or r['name'])
    tr=list(TR.get(lab,[]))
    if d=='new-sarpy' and r['project_id'].startswith('2-') and 'under cn rr' in r['name'].lower(): tr+=TR.get('new-sarpy 2-x (CN RR crossings)',[])
    base['parish_report_2026_07_31']=' || '.join(tr)
    base['links']=' '.join(M[f]['url'] for f in hit[5]) if hit else ''
    if hit:
        base.update(status=hit[3],built_scope=hit[4],parish_source=src(hit[5]),parish_source_date=last(hit[5]),independent_source=hit[7],independent_source_date=hit[8],notes=hit[6])
    else:
        base.update(status='No record found',built_scope='',parish_source='',parish_source_date='',independent_source='',independent_source_date='',
          notes='Searched: Legistar matter titles 2020-01-01 to '+AS_OF+' (index/legistar_matters.csv).')
    out.append(base)
for i,m in enumerate(MATCH):
    if not used[i]: sys.exit(f'unmatched rule {m[:3]}')
F=['doc','page','table','project_id','row','name','plan_cost','status','built_scope','parish_source','parish_source_date','independent_source','independent_source_date','as_of','notes','parish_report_2026_07_31','links']
with open(SK/'index/status.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=F); w.writeheader(); w.writerows(out)
print(len(out),'rows;',len(skip),'deck rows skipped'); print(collections.Counter(o['status'] for o in out))
for i,m in enumerate(MATCH): print(used[i],m[0],m[1],m[2])
