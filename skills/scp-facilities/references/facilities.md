# St. Charles Parish facility roster

Generated 2026-11-03 by `scripts/facilities.py roster --md`. Don't edit by hand; rebuild it.

Sources: LDEQ EDMS AI search (1366 AIs in the parish), EPA ECHO active facilities for FIPS 22089 (393 rows), EPA FRS program IDs for the selected rows, and RMP filings from the Data Liberation Project's FOIA copy of EPA's database.

**How to read it.**

- A row means a site is registered, not that it is operating. The names are the agencies' and can lag a sale, so EPA's name for a record can be a past owner's.
- **EPA active:** ECHO lists an active permit or program on a record that is this AI's alone or in this company's name. A permit can outlast production.
- **On a shared EPA record, not in this company's name:** EPA tracks a whole complex under one registry ID, marked (shared), and this AI shares a permit ID with it. That says nothing about this tenant's own status.
- **LDEQ AI only:** no selected ECHO record links here. It can be a new, proposed, closed or renamed site, so check it with `bayou:ldeq-permit-status` or LDEQ's Check Permit Status page.
- **joined by address:** no shared permit ID, only a matching street number and name. Confirm it.
- **RMP filings** are listed by address and aren't assigned to a company, because several companies can share an address. Read the filing's own name.
- Selected by rule: LDEQ's chemical, refining and pipeline types, a short list of named power and terminal sites, and ECHO rows with a TRI ID, a greenhouse gas flag, an industrial SIC code or a live RMP filing at the address. A site outside that rule isn't here, so use `find`.

## Addresses with more than one LDEQ AI

### 355 Hwy 3142

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 169315 | Arkema Inc - Arkema St Charles | 110041625202 ARKEMA INC | EPA active |
| 242670 | Dow Infraco LLC - St Charles Operations | 110018861793 UNION CARBIDE CORP - ST CHARLES PLANT (shared) | On a shared EPA record, not in this company's name |
| 121058 | Kaneb Pipe Line Operating Partnership LP - Dow Chemical Taft Ammonia Terminal | 110018861793 UNION CARBIDE CORP - ST CHARLES PLANT (shared) | On a shared EPA record, not in this company's name |
| 199443 | MMP SCO LLC | 110069461530 MMP SCO LLC | EPA active |
| 2083 | Union Carbide Corp - St Charles Operations | 110018861793 UNION CARBIDE CORP - ST CHARLES PLANT (shared) | EPA active |
| 242817 | Union Carbide Corporation - St Charles Operations | 110018861793 UNION CARBIDE CORP - ST CHARLES PLANT (shared) | EPA active |
| 227637 | Vopak Industrial Infrastructure Americas St Charles LLC - Vopak Terminal St. Charles | 110018861793 UNION CARBIDE CORP - ST CHARLES PLANT (shared); 110071062771 VOPAK INDUSTRIAL INFRASTRUCTURE AMERICAS ST. CHARLES LLC - VOPAK TERMIAL ST. CHA | EPA active |

RMP filings at this address: 100000094211 St. Charles Operations (validated 2024-02-19); 100000211488 Arkema Inc (validated 2025-05-29); 100000245941 Vopak Terminal St. Charles (validated 2025-08-18).

### 11842 River Rd

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 228169 | Arq St. Rose LLC - Arq St Rose | - | LDEQ AI only |
| 4885 | International Matex Tank Terminals LLC - St. Rose Terminal | 110000448944 ST ROSE REFINERY LLC - ST ROSE REFINERY (shared); 110071071590 INTERNATIONAL-MATEX TANK TERMINALS (ST. ROSE) | EPA active |
| 147551 | REG Inc - St Rose Biodiesel Production Plant | 110028007323 REG INC - ST ROSE BIODIESEL PRODUCTION PLANT | EPA active |
| 236110 | St Charles Clean Fuels LLC - Blue Ammonia Facility | - | LDEQ AI only |
| 3462 | St Rose Refinery LLC - St Rose Refinery | 110000448944 ST ROSE REFINERY LLC - ST ROSE REFINERY (shared) | EPA active |

RMP filings at this address: 100000088228 St. Rose Facility (validated 2017-11-22; deregistered 2018-08-03).

### 12501 River Rd

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 170668 | Air Products & Chemicals Inc - Luling Hydrogen Plant | 110015670521 BAYER CROPSCIENCE LP - LULING SITE (shared); 110055498956 AIR PRODUCTS & CHEMICALS INC LULING SMR | EPA active |
| 105475 | Bridgeline Holdings LP - Monsanto Meter Station | - | LDEQ AI only |
| 17605 | Rhodia Inc APAP Plant | 110015670521 BAYER CROPSCIENCE LP - LULING SITE (shared) | On a shared EPA record, not in this company's name |
| 1096 | Ruveon LLC - Luling Facility | 110015670521 BAYER CROPSCIENCE LP - LULING SITE (shared) | On a shared EPA record, not in this company's name |

RMP filings at this address: 100000126561 Bayer CropScience LP, Luling Site (validated 2023-06-28); 100000216857 Air Products, Luling H2 (validated 2025-09-12).

### 17420 River Rd

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 205189 | CB&I LLC - St Charles Power Station CCP | 110070050266 CB&I LLC | EPA active |
| 197303 | Entergy Louisiana LLC - J Wayne Leonard Power Station | 110071499114 ENTERGY LOUISIANA LLC - J WAYNE LEONARD POWER STATION | EPA active |
| 687 | Entergy Louisiana LLC - Little Gypsy Generating Plant/J Wayne Leonard Power Station | 110007291652 ENTERGY LOUISIANA LLC - LITTLE GYPSY GENERATING PLANT (shared) | EPA active |
| 163246 | Shaw Constructors Inc - Little Gypsy Plant | 110007291652 ENTERGY LOUISIANA LLC - LITTLE GYPSY GENERATING PLANT (shared) | On a shared EPA record, not in this company's name |

### 15536 River Rd

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 1406 | Equilon Enterprises LLC - Norco Refinery | 110013831201 NORCO MANUFACTURING COMPLEX & ASSOCIATED FACILITIES (shared) | On a shared EPA record, not in this company's name |
| 26336 | Shell Chemical LP - Norco Chemical Plant – East Site | 110013831201 NORCO MANUFACTURING COMPLEX & ASSOCIATED FACILITIES (shared); 110071940897 MOTIVA ENTERPRISES, LLC - NORCO, LA REFINERY | EPA active |
| 19276 | Shell Chemical LP - Shell Chemical LP Norco Cypress Site | 110013831201 NORCO MANUFACTURING COMPLEX & ASSOCIATED FACILITIES (shared) | On a shared EPA record, not in this company's name |

RMP filings at this address: 100000026009 Equilon Enterprises LLC dba Shell-NORCO LA REFINER (validated 2023-12-13).

### 15849 Old Spanish Trail

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 192456 | Chevron Pipe Line Co - Paradis Gas Processing Plant | 110000555710 PARADIS GAS PROCESSING PLANT (shared) | On a shared EPA record, not in this company's name |
| 104090 | Discovery Producer Services LLC - Discovery Paradis Fractionation Plant | 110000555710 PARADIS GAS PROCESSING PLANT (shared) | On a shared EPA record, not in this company's name |
| 40853 | Phillips 66 Pipeline LLC - Paradis Pump Station | 110000555710 PARADIS GAS PROCESSING PLANT (shared) | On a shared EPA record, not in this company's name |

RMP filings at this address: 100000114226 Discovery Producer Services: Paradis Fractionator (validated 2024-09-25).

### 16122 River Rd

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 4384 | Shell Chemical LP - Norco Chemical Plant West Site | 110013662009 MOMENTIVE SPECIALTY CHEMICALS INC (shared); 110024471668 NORCO CHEMICAL PLANT - WEST SITE | EPA active |
| 87883 | Shell Chemical LP - Norco West Site Facility | 110013662009 MOMENTIVE SPECIALTY CHEMICALS INC (shared) | On a shared EPA record, not in this company's name |
| 25156 | W R Grace & Co - Conn - Super High Activity Catalyst Plant | 110013662009 MOMENTIVE SPECIALTY CHEMICALS INC (shared); 110071722803 W R GRACE & CO - CONN - SUPER HIGH ACTIVITY CATALYST PLANT | EPA active |

RMP filings at this address: 100000088157 Shell Norco Chemical Plant - West Site (validated 2023-12-13); 100000139824 Super High Activity Catalyst (SHAC) Plant (validated 2024-12-13); 100000177523 Hexion Inc. Norco Facility (validated 2016-12-30; deregistered 2017-01-30).

### 10352 River Rd

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 25710 | Safety-Kleen System Inc | 110017758363 DELTA PETROLEUM COMPANY INCORPORATED (shared) | On a shared EPA record, not in this company's name |
| 172371 | Shell Chemical LP - Delta Petro | 110017758363 DELTA PETROLEUM COMPANY INCORPORATED (shared) | On a shared EPA record, not in this company's name |

### 14902 River Rd

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 195909 | Valero Partners LA LLC - St Charles Terminal | 110000448659 VALERO ST. CHARLES REFINERY AND TERMINAL (shared) | EPA active |
| 26003 | Valero Refining - New Orleans LLC - St Charles Refinery | 110000448659 VALERO ST. CHARLES REFINERY AND TERMINAL (shared); 110055569567 AIR PRODUCTS & CHEMICALS INC - NORCO HYD (shared); 110070824567 VALERO REFINING- NEW ORLEANS LLC: ST CHARLES REFINERY | EPA active |

RMP filings at this address: 100000093409 Valero St. Charles Refinery and Terminal (validated 2022-07-28).

### 17705 River Rd

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 83898 | Entergy Louisiana LLC - Waterford 1 & 2 Electric Generating Plant | 110000732388 ENTERGY LOUISIANA LLC - WATERFORD 1 & 2 ELECTRIC GENERATING PLANT | EPA active |
| 248424 | Entergy Louisiana LLC - Waterford Advanced Power Station Units 5 & 6 | - | LDEQ AI only |

### 261 Hwy 3142

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 38399 | Linde Gas & Equipment Inc - Taft Site | 110000743303 PRAXAIR INC (shared); 110064033594 PRAXAIR DISTRIBUTION INC. | EPA active |
| 8853 | Praxair Inc | 110000743303 PRAXAIR INC (shared) | EPA active |

RMP filings at this address: 100000130084 Linde Gas & Equipment - Hahnville (validated 2023-11-15).

### 266 Hwy 3142

| LDEQ AI | LDEQ name | EPA registry ID and name | Records |
|---|---|---|---|
| 32778 | Koch Fertilizer LLC - Taft Terminal | 110022523660 KOCH NITROGEN CO LLC-TAFT TERMINAL | EPA active |
| 1137 | Occidental Chemical Corp - Taft Plant | 110000597113 TAFT COGENERATION FACILITY (shared); 110000743296 OCCIDENTAL CHEMICAL CORP - TAFT PLANT | EPA active |

RMP filings at this address: 100000046666 Koch Fertilizer, LLC - Taft Terminal (validated 2025-11-17); 100000081911 Occidental Chemical Corporation Taft Plant (validated 2024-06-12).

## Addresses with one LDEQ AI

| Address | LDEQ AI | LDEQ name | EPA registry ID and name | Records | RMP filings at this address |
|---|---|---|---|---|---|
| 10425 Airline Hwy | 202356 | Baker Petrolite LLC | - | LDEQ AI only | - |
| 12466 River Rd | 1738 | Bunge Chevron Ag Renewables LLC - Destrehan Oilseed Processing Facility | 110000448640 BUNGE CORPORATION | EPA active | - |
| 12513 Queenie Rd | 191532 | Valentra Industrial Products LLC - Luling Facility | 110066956299 VALENTRA INDUSTRIAL PRODUCTS LLC - LULING FACILITY | EPA active | 100000231448 Valentra Industrial Products, LLC (validated 2025-12-05) |
| 1268 Hwy 3127 | 5034 | Barriere Construction Co LLC - Boutte Asphalt Plant #625 | 110003312727 BARRIERE CONSTRUCTION CO LLC - BOUTTE ASPHALT PLANT #625 | EPA active | - |
| 14885 Airline Dr | 180618 | Air Products & Chemicals Inc - Norco Hydrogen Plant | 110055569567 AIR PRODUCTS & CHEMICALS INC - NORCO HYD (shared) | EPA active | 100000225133 Air Products and Chemicals Norco Hydrogen Plant (validated 2024-05-24) |
| 14891 E Airline Hwy | 168018 | Diamond Green Diesel LLC - Green Diesel Plant | 110045975744 DIAMOND GREEN DIESEL | EPA active | 100000219649 Diamond Green Diesel LLC (validated 2021-08-13) |
| 15601 Airline Hwy | 99403 | Shell Pipeline Co LP - Norco Pump Station | - | LDEQ AI only | - |
| 15608 Hwy 61 | 51546 | Enterprise Gas Processing LLC - Norco Fractionation Plant | 110015604283 NORCO FRACTIONATION PLANT | EPA active | - |
| 16991 River Rd | 122487 | Air Products & Chemicals Inc - Taft I Hydrogen Recovery Plant | 110017761153 AIR PRODUCTS & CHEMICALS INC - TAFT I HY | EPA active | - |
| 17245 River Rd | 2720 | Mosaic Fertilizer LLC - Taft Plant | 110000448702 MOSAIC FERTILIZER LLC - TAFT PLANT | EPA active | 100000137513 Taft Plant (validated 1999-07-16; deregistered 1999-10-28) |
| 17265 River Rd | 35260 | Entergy Operations Inc - Waterford 3 Steam Electric Station | 110002042414 ENTERGY LOUISIANA LLC - WATERFORD 3 STEAM ELECTRIC STATION | EPA active | - |
| 177 Hwy 3142 | 117691 | Air Liquide Large Industries US LP - Taft ASU | 110015785676 AIR LIQUIDE LARGE INDUSTRIES US LP - TAFT ASU | EPA active | - |
| 201James Dr E | 10940 | PPG Finishes | - | LDEQ AI only | - |
| 207 Hwy 3142 | 25735 | Western International Gas & Cylinders Inc - Taft | 110072081438 WESTERN INTERNATIONAL GAS & CYLINDERS INC - TAFT | EPA active | 100000188405 Western International Gas - Hahnville (validated 2024-06-20) |
| 211 Cedar Dr | 3483 | Air Liquide Large Industries US LP - Norco ASU Plant | 110000597140 AIR LIQUIDE LARGE INDUSTRIES U.S. LP | EPA active | - |
| 29.9298 - 90.3359 | 212772 | Shell Pipeline Company LP Clovelly to Norco Luling Valve Site | - | LDEQ AI only | - |
| 301 Third St | 43359 | St Charles Parish Waterworks District #2 - West Bank Plant | 110000576181 ST. CHARLES PARISH WATERWORKS DISTRICT 2 | EPA active | 100000102827 St. Charles Parish Waterworks District 2 (validated 2022-03-24) |
| 400 Esperanza Plantation Rd | 134843 | Amrize South Central Inc - Luling Ready Mix Plant | 110022523679 LAFARGE LULING RMX | EPA active | - |
| 40th Ave | 176780 | Hydrogen Plant - S&B Engineers & Constructors Ltd | 110056382463 PRAXAIR, ST. CHARLES FACILITY (shared) | On a shared EPA record, not in this company's name | - |
| 470 Queeny Rd 1.6 Mi S of | 28032 | Gulf South Pipeline Co - Monsanto Meter Station | 110010377314 GULF SOUTH PIPELINE CO - MONSANTO METER STATION | EPA active | - |
| 471 Hwy 3142 | 2706 | Galata Chemicals LLC - Taft Facility | 110000602465 GALATA CHEMICALS, LLC | EPA active | 100000065822 Galata Chemicals - Taft Facility (validated 2021-01-20) |
| 473 Hwy 3142 | 583 | Chemtura Corp - Taft Facility | 110000597113 TAFT COGENERATION FACILITY (shared) | On a shared EPA record, not in this company's name | 100000123403 Shell Chemical Company Inc. Taft Plant (validated 1999-07-13; deregistered 2003-02-05) |
| 538 Prospect Ave | 204446 | Valero Terminaling & Distribution Co - Norco Pump Station | 110070262721 VALERO TERMINALING & DISTRIBUTION CO - NORCO PUMP STATION | EPA active | - |
| 5900 Hwy 3127 | 92039 | Waste Pro of Louisiana Inc | 110012313335 ST CHARLES KILLONA | EPA active | - |
| 600 Judge Edward Dufresne Pkwy | 215737 | Entergy Louisiana LLC - Entergy Luling Service Center | 110070555022 ENTERGY LOUISIANA LLC - ENTERGY LULING SERVICE CENTER | EPA active | - |
| 700 S River Rd | 12333 | Air Products & Chemicals Inc - Luling Plant | - | LDEQ AI only | - |
| 801 Prospect Ave | 44866 | Rain CII Carbon LLC - Norco Coke Calcining Plant | 110022810449 RAIN CII CARBON LLC - NORCO COKE PLANT | EPA active | - |
| Cedar Dr & Hwy 61 | 237350 | ChemTreat | - | LDEQ AI only | - |
| E corner Prospect Ave & 40th Ave | 175302 | Linde Inc - Linde St Charles Plant | 110056382463 PRAXAIR, ST. CHARLES FACILITY (shared); 110071722719 LINDE INC - LINDE ST CHARLES PLANT | EPA active | - |
| Hwy 48 2.3 Mi E of Hwy 310 | 159884 | Shell Oil Co LP - I.M.T.T. Station | 110037582817 SHELL OIL CO LP - I.M.T.T. STATION | EPA active | - |
| Hwys 18 & 3142 | 32777 | Air Products & Chemicals Inc - Taft II Hydrogen Recovery Plant | 110002068841 AIR UUC HYDROGEN RECOVERY | EPA active | - |
| Lot 1B2B Riverbend | 103790 | X Chem Inc - St Rose Facility | - | LDEQ AI only | - |
| Mississippi RM 131 | 192221 | AM Agrigen Industries LLC - AMAI Ammonia & Urea Plant | - | LDEQ AI only | - |
| near Hwy 3142, approx 2.18mi W of | 250934 | Swift Fuels LLC - Light Gas to Fuels Plant (LG2F) | - | LDEQ AI only | - |
| No street address | 115991 | Shell Pipeline Co LP - Taft Lateral to the Norco - Avondale Pipeline - Construction | - | LDEQ AI only | - |
| Shell Refinery | 91088 | Gulf South Pipeline Co LP - Condensate Tank | - | LDEQ AI only | - |

## RMP filings with no roster address

RMP addresses are the filer's, and many differ from LDEQ's for the same plant.

| RMP filing | Address |
|---|---|
| 100000147183 Destrehan Wastewater Treatment Plant (validated 1999-07-22; deregistered 2000-12-11) | Johnathan Street / 1 mile North of LA Hwy. 48 |
| 100000252745 J. Wayne Leonard Power Station (validated 2024-11-11) | 17494 River Road |
| 100000221636 Linde -  St. Charles (validated 2023-05-15) | Prospect Ave / Post 2 / Valero Refinery |
| 100000176098 Luling Oxidation Pond (validated 2025-01-16) | Texaco Road / 2.5 miles South of US Highway 90 |
| 100000005665 Norco Fractionation Plant (validated 2025-03-06) | 15608 Airline Highway / (U.S. Hwy 61) |
| 100000124091 Norco, LA (validated 1999-07-13; deregistered 2002-03-13) | Cedar Street / P.O. Box 336 |
| 100000088282 Shell Norco Chemical Plant - East Site (validated 2023-12-13) | 15136 River Road |
| 100000127132 St. Charles Operations Cypress Polypropylene Plant (validated 2007-07-17; deregistered 2008-05-16) | 901 Prospect Ave. |
| 100000102738 St. Charles Parish Waterworks District 1 (validated 2022-03-24) | 14924 River Road |

## EPA rows with no single LDEQ match

| EPA registry ID | EPA name | Address |
|---|---|---|
| 110071043384 | BOUTTE ASPHALT PLANT | 1268 LA HWY 3127, BOUTTE |
| 110071995701 | HARVEY CLEARY - DOW SCO MANUFACTURING & CONSOLIDATED LAB BUILDINGS | 355 HWY 3142, HAHNVILLE |
| 110020053573 | OCCIDENTAL CHEMICAL CORP  - LULING | 12501 RIVER RD., LULING |
| 110000553124 | ST. CHARLES PARISH WATERWORKS DISTRICT 1 | 14924 RIVER ROAD, NORCO |

## Left out

11 of ECHO's parish rows name a town outside the parish, or none, so they weren't selected. Check any you need by hand: Alexandria, Baton Rouge, Gonzales, Houston, Jean Lafitte, La Place, Laplace, Statewide, Westwego.
