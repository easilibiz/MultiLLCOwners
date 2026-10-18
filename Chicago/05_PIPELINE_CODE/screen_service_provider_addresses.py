from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path


AS_OF_DATE = "2026-08-28"
ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "03_PROCESSED" / "chicago_msa_partial_cook_kendall_20260828_address_clusters.csv"
ALL_OUTPUT = ROOT / "03_PROCESSED" / "chicago_msa_partial_service_screen_all_20260828.csv"
FINAL_DIR = ROOT / "01_FINAL_OUTPUTS"


KNOWN_SERVICE_ADDRESSES = {
    "5773 N LINCOLN|CHICAGO|IL|60659": (
        "LAW_FIRM", "Gallagher Niemeyer & Abrams law firm publishes this exact address.",
        "https://www.gn-lawyers.com/", "HIGH"
    ),
    "150 N MICHIGAN|#2700|CHICAGO|IL|60601": (
        "LAW_FIRM_REGISTERED_AGENT", "Clark Hill PLC and a registered-agent listing use this exact suite.",
        "https://www.elfaonline.org/docs/default-source/directories/2016legalbuyersguide.pdf?sfvrsn=2", "HIGH"
    ),
    "2815 W ROSCOE|CHICAGO|IL|60618": (
        "PROPERTY_MANAGER", "Peak Properties publishes this exact address as its office.",
        "https://www.peakproperties.biz/faq", "HIGH"
    ),
    "107 GREEN BAY|WILMETTE|IL|60091": (
        "PROPERTY_MANAGER_LAWYER", "Wilmette Real Estate & Management and a lawyer listing use this exact address.",
        "https://www.bbb.org/us/il/wilmette/profile/real-estate/wilmette-real-estate-mgmt-0654-16002933", "MEDIUM"
    ),
    "549 W RANDOLPH|FL2|CHICAGO|IL|60661": (
        "PROPERTY_MANAGER", "Pangea Properties publishes this exact office address.",
        "https://www.pangeaproperties.com/contact/", "HIGH"
    ),
    "549 W RANDOLPH|#2|CHICAGO|IL|60661": (
        "PROPERTY_MANAGER", "Pangea Properties publishes this exact office address.",
        "https://www.pangeaproperties.com/contact/", "HIGH"
    ),
    "4228 N MILWAUKEE|CHICAGO|IL|60641": (
        "PROPERTY_MANAGER", "MPR Property Management is listed at this exact address.",
        "https://www.waze.com/live-map/directions/us/il/chicago/mpr-property-management?to=place.ChIJ-9CeWj_MD4gRj2ZlZu36faY", "MEDIUM"
    ),
    "2348 W GRAND|CHICAGO|IL|60612": (
        "REAL_ESTATE_AGENT", "Chicago Properties publishes this exact address for its agent team.",
        "https://www.chiprop.com/agents/", "HIGH"
    ),
    "41 CHICAGO|OAK PARK|IL|60302": (
        "PROPERTY_MANAGER", "Mastercare Building Services publishes this exact address and property-management services.",
        "https://www.mcareservices.com/", "HIGH"
    ),
    "1922 N WOOD|CHICAGO|IL|60622": (
        "PROPERTY_MANAGER", "Hanging Out publishes this exact address for its rental/property-management operation.",
        "https://hangingout.net/contact_us", "HIGH"
    ),
    "640 N LASALLE|#638|CHICAGO|IL|60654": (
        "PROPERTY_MANAGER_REGISTERED_AGENT", "Pangea-related real-estate management and registered-agent evidence uses this suite.",
        "https://uspto.report/TM/86033953", "MEDIUM"
    ),
    "324 W TOUHY|PARK RIDGE|IL|60068": (
        "REAL_ESTATE_AGENT_ACCOUNTING", "An @properties office and PR Accounting are listed at this exact address.",
        "https://www.waze.com/en-GB/live-map/directions/us/il/park-ridge/%40properties?to=place.ChIJS_BPDSjJD4gRvTkOQeB4EgM", "MEDIUM"
    ),
    "3215 W FULLERTON|CHICAGO|IL|60647": (
        "PROPERTY_MANAGER", "M. Fishman & Company publishes this exact address and leasing/property-management operation.",
        "https://www.mfishmanco.com/vacancies", "HIGH"
    ),
    "55 E JACKSON|#500|CHICAGO|IL|60604": (
        "PROPERTY_MANAGER_LAW_FIRM", "Marc Realty and a law firm publish this exact suite.",
        "https://cases.stretto.com/public/x319/12693/PLEADINGS/1269307052480000000823.pdf", "HIGH"
    ),
    "3654 N LINCOLN|CHICAGO|IL|60613": (
        "PROPERTY_MANAGER", "Chicago Apartment Place is licensed/listed at this exact address as a residential property manager.",
        "https://data.cityofchicago.org/api/views/ims6-wtmx/rows.pdf?app_token=U29jcmF0YS0td2VraWNrYXNz0", "HIGH"
    ),
    "2320 N DAMEN|CHICAGO|IL|60647": (
        "PROPERTY_MANAGER", "Beal Properties publishes this exact office address for leasing and property management.",
        "https://www.bealproperties.com/apartments/chicago/lincoln-square-ravenswood/4851-n-damen/", "HIGH"
    ),
    "2320 N DAMEN|#1D|CHICAGO|IL|60647": (
        "PROPERTY_MANAGER", "Beal Properties publishes this exact office address for leasing and property management.",
        "https://www.bealproperties.com/apartments/chicago/lincoln-square-ravenswood/4851-n-damen/", "HIGH"
    ),
    "2506 N CLARK|#101|CHICAGO|IL|60614": (
        "PROPERTY_MANAGER", "HUD-derived records identify the management agent at this exact suite.",
        "https://friendlylandlord.com/section-8-apartments/detail?property_id=800006233", "MEDIUM"
    ),
    "3324 W NORTH|CHICAGO|IL|60647": (
        "PROPERTY_MANAGER", "Icon Property Management is listed at this exact address as a residential property manager.",
        "https://naicslist.com/company-profile/icon-property-management-llc-chicago-il-60647", "MEDIUM"
    ),
    "425 W NORTH|CHICAGO|IL|60610": (
        "REAL_ESTATE_AGENT", "Jameson Sotheby's real-estate agents publish this exact address.",
        "https://members.lakeviewroscoevillage.org/list/member/jameson-sotheby-s-international-realty-ben-shalom-chicago-5382", "HIGH"
    ),
    "4818 N DAMEN|CHICAGO|IL|60625": (
        "PROPERTY_MANAGER_REAL_ESTATE_AGENT", "Winnemac Properties is listed at this exact address as property management and a real-estate agency.",
        "https://www.realtor.com/realestateagency/589e43c0cb0a7c0011dafeba", "MEDIUM"
    ),
    "2241 W HOWARD|CHICAGO|IL|60645": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "@properties and Universal Realty Group are listed at this exact address.",
        "https://www.waze.com/live-map/directions/us/il/chicago/%40-properties-christies-international-real-estate?to=place.ChIJHbcPatLPD4gRmZYfDoStl3g", "MEDIUM"
    ),
    "9440 ENTERPRISE|MOKENA|IL|60448": (
        "REAL_ESTATE_BROKER_PROPERTY_MANAGER", "Location Finders Brokerage publishes this exact address and advertises brokerage and property-management services.",
        "https://www.loopnet.com/company/location-finders-brokerage-llc/v8382vel/", "HIGH"
    ),
    "2211 N ELSTON|#304|CHICAGO|IL|60614": (
        "REAL_ESTATE_AGENT_DEVELOPER", "A real-estate agent and GW Properties publish this exact suite.",
        "https://www.realtor.com/realestateagents/56cf7eaa89a68901006ff60f", "HIGH"
    ),
    "1 N WACKER|#4125|CHICAGO|IL|60606": (
        "LAW_FIRM", "A law office is listed at this exact suite.",
        "https://www.lawyersattorneysguide.com/law-office/illinois/chicago/office-255984115/", "MEDIUM"
    ),
    "542 S DEARBORN|#900|CHICAGO|IL|60605": (
        "LAW_FIRM", "Court filings identify Rachlis Duff Peel & Kaplan at this exact suite.",
        "https://www.rdaplaw.net/wp-content/uploads/sites/1103921/2024/06/190913-Receivers-Second-Motion-To-Approve-Sale-as-filed.pdf", "HIGH"
    ),
    "4520 N CLARENDON|CHICAGO|IL|60640": (
        "PROPERTY_MANAGER_REAL_ESTATE_AGENT", "Becovic publishes this exact address as its management and service office.",
        "https://becovic.com/our-story/becovic-management-division/", "HIGH"
    ),
    "2156 N HALSTED|CHICAGO|IL|60614": (
        "PROPERTY_MANAGER_REAL_ESTATE_BROKER", "Glascott & Associates is listed at this exact address as a real-estate broker and property manager.",
        "https://bizstanding.com/p/glascott%2Band%2Bassociates%2Binc-167562295", "MEDIUM"
    ),
    "4554 N MAPLEWOOD|CHICAGO|IL|60625": (
        "PROPERTY_MANAGER", "Bertsch Properties is listed at this exact address as a property-management company.",
        "https://prospeo.io/c/bertsch-properties", "MEDIUM"
    ),
    "6348 N CICERO|CHICAGO|IL|60646": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "Devon Realty and Devon Property & Management are listed at this exact address.",
        "https://bizstanding.com/directory/IL/DE/1115/", "MEDIUM"
    ),
    "5277 TRILLIUM|HOFFMAN ESTS|IL|60192": (
        "PROPERTY_MANAGER", "Government records identify Heidner Property Management at this exact address.",
        "https://www.villageofschaumburg.com/home/showpublisheddocument/2382/637267975106700000", "HIGH"
    ),
    "1 W DUNDEE|#200|BUFFALO GRV|IL|60089": (
        "PROPERTY_MANAGER_ASSET_MANAGER", "Svigos Asset Management publishes this exact suite and property-management services.",
        "https://svigos.com/wp-content/uploads/2020/12/FORM-Landlord-Verification-2020.pdf", "HIGH"
    ),
    "4355 N RAVENSWOOD|CHICAGO|IL|60613": (
        "REAL_ESTATE_RENTAL_AGENT", "A property-rental agency is listed at this exact address.",
        "https://www.mapquest.com/us/illinois/creative-designs-7730525", "MEDIUM"
    ),
    "4441 N MILWAUKEE|CHICAGO|IL|60630": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "Optimus Realty publishes this exact address for leasing, rentals and tenant management.",
        "https://www.optimusrealty.com/current-tenants", "HIGH"
    ),
    "2533 W FULLERTON|CHICAGO|IL|60647": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "The Apartment Source publishes this exact office and describes leasing, sales and property-management services.",
        "https://apartmentsource.com/blog/apartment-source-2020-recap/", "HIGH"
    ),
    "105 W MADISON ST 1401|CHICAGO|IL|60602": (
        "REAL_ESTATE_AGENT", "Windy City RE publishes this exact suite as its office.",
        "https://images2.loopnet.com/d2/cX7pfM7Wk5XQYRsd-9CeYn6uHLau4Rqh47EfvsPvBbU/document.pdf", "MEDIUM"
    ),
    "640 N LASALLE 638|CHICAGO|IL|60654": (
        "PROPERTY_MANAGER_REGISTERED_AGENT", "This is an address-format variant of the researched Pangea/registered-agent suite 638.",
        "https://uspto.report/TM/86033953", "MEDIUM"
    ),
    "2320 N DAMEN 1D|CHICAGO|IL|60647": (
        "PROPERTY_MANAGER", "This is an address-format variant of Beal Properties' researched office suite 1D.",
        "https://www.bealproperties.com/apartments/chicago/lincoln-square-ravenswood/4851-n-damen/", "HIGH"
    ),
    "1110 PLEASANT|OAK PARK|IL|60302": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "R.P. Fox & Associates is listed at this exact address as a real-estate agent and property operator.",
        "https://www.downtownoakpark.net/dtopba/", "HIGH"
    ),
    "1110 PLEASANT|#212|OAK PARK|IL|60302": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "This suite is part of the researched R.P. Fox & Associates real-estate office address.",
        "https://www.downtownoakpark.net/dtopba/", "HIGH"
    ),
    "1950 W MONTROSE|CHICAGO|IL|60613": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "Rany Management publishes this exact address and identifies itself as Realtors and property managers.",
        "https://business.ravenswoodchicago.org/list/member/rany-management-chicago-773-728-9000-1136", "HIGH"
    ),
    "1950 W MONTROSE AVE 1|CHICAGO|IL|60613": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "This address-format variant is associated with the researched Rany Management office.",
        "https://business.ravenswoodchicago.org/list/member/rany-management-chicago-773-728-9000-1136", "MEDIUM"
    ),
    "1950 W MONTROSE|#1|CHICAGO|IL|60613": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "This unit-format variant is associated with the researched Rany Management office.",
        "https://business.ravenswoodchicago.org/list/member/rany-management-chicago-773-728-9000-1136", "MEDIUM"
    ),
    "2 ETHEL|#205A|EDISON|NJ|08817": (
        "REAL_ESTATE_CONSULTANT", "Excel Property Consulting publishes this exact suite for its real-estate consulting operation.",
        "https://www.slideshare.net/slideshow/excel-property-consulting/63412902", "HIGH"
    ),
    "2000 N RACINE|#4400|CHICAGO|IL|60614": (
        "PROPERTY_MANAGER_REAL_ESTATE_AGENT", "Kass Management Services publishes this exact suite and advertises property management and leasing services.",
        "https://kassmanagement.com/office-commercial/2000-n-racine", "HIGH"
    ),
    "2000 N RACINE AVE 4400|CHICAGO|IL|60614": (
        "PROPERTY_MANAGER_REAL_ESTATE_AGENT", "This address-format variant is the researched Kass Management Services office suite 4400.",
        "https://kassmanagement.com/office-commercial/2000-n-racine", "HIGH"
    ),
    "5339 W BELMONT|CHICAGO|IL|60641": (
        "PROPERTY_MANAGER", "Beaulieu Management publishes this exact address as its rental-management office.",
        "https://www.beaulieurental.com/contact-us", "HIGH"
    ),
    "687 N MILWAUKEE|CHICAGO|IL|60642": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "Safe Harbor Realty is listed at this exact address as a real-estate office providing property-management and leasing services.",
        "https://www.realty.com/office/153365/safe_harbor_realty_llc", "HIGH"
    ),
    "1030 N CLARK|#300|CHICAGO|IL|60610": (
        "REAL_ESTATE_BROKER_PROPERTY_MANAGER", "The Lord Companies publishes this exact suite for its brokerage, development, investment and consulting operation.",
        "https://images3.loopnet.com/d2/wZb1nXFnfQTazgST0HbQYc19ip7Rf-e3ZXk9Ho8iy6I/document.pdf", "HIGH"
    ),
    "1010 HILLSIDE|NORTHBROOK|IL|60062": (
        "REAL_ESTATE_AGENT_PROPERTY_MANAGER", "A licensed real-estate agent and River North Realty publish this exact address; city records also identify Fakhoury Property Management there.",
        "https://www.realtor.com/realestateagents/657dd8d4ae101f006f60cdb3", "HIGH"
    ),
    "2211 YORK|#222|OAK BROOK|IL|60523": (
        "PROPERTY_TAX_CONSULTANT", "County tax records identify Marvin F. Poer & Co., a property-tax consulting intermediary, at this exact suite.",
        "https://tax.lakecountyil.gov/Datalets/Datalet.aspx?State=1%7C3%7C1%7C1%7C1%7C1%7C1%7C&UseSearch=no&card=2&item=1&items=6&jur=049&mode=conveyance&pin=1633300026&taxyr=2026", "HIGH"
    ),
    "200 N LASALLE|#2350|CHICAGO|IL|60601": (
        "REAL_ESTATE_BROKER_PROPERTY_MANAGER", "Matanky Realty Group publishes this exact suite for brokerage and third-party property-management services.",
        "https://matanky.com/contact-us/", "HIGH"
    ),
    "814 COMMERCE DR S300|OAK BROOK|IL|60523": (
        "PROPERTY_MANAGER_REAL_ESTATE_BROKER", "Court records identify Pine Tree Commercial Realty and IRC property-management operations at this exact suite.",
        "https://www.veritaglobal.net/americansignature/document/2512105260106000000000144", "HIGH"
    ),
    "2432 N CLYBOURN|CHICAGO|IL|60614": (
        "REAL_ESTATE_BROKER_PROPERTY_MANAGER", "Moran Realty and Bil-Mar Management publish this exact address for brokerage and property-management services.",
        "https://www.moranrealty.net/", "HIGH"
    ),
    "219 E IRVING PARK|ROSELLE|IL|60172": (
        "REAL_ESTATE_BROKER_PROPERTY_MANAGER", "GC Realty & Development publishes this exact address and advertises third-party property-management services.",
        "https://www.gcrealtyinc.com/chicago-ridge-property-management", "HIGH"
    ),
}


KNOWN_OWNER_OPERATOR_ADDRESSES = {
    "516 N OGDEN|#137|CHICAGO|IL|60642": (
        "OWNER_OPERATOR", "Tax and business records connect MO2 Properties and its real-estate holdings to this office; no third-party professional-service signal found.",
        "https://naicslist.com/company-profile/mo2-properties-llc-chicago-il-60642", "MEDIUM"
    ),
    "666 DUNDEE|#1102|NORTHBROOK|IL|60062": (
        "OWNER_DEVELOPER", "Public development disclosures identify Brinshore entities and ownership interests at this business address.",
        "https://occprodstoragev1.blob.core.usgovcloudapi.net/lsmatterattachmentspublic/cba76fcd-7377-44c1-97f0-7d04c738b2f6.pdf", "HIGH"
    ),
    "1517 W HADDON|CHICAGO|IL|60642": (
        "OWNER_OPERATOR", "City and tax records identify LLC owners and their mailing address here; no intermediary signal found.",
        "https://reportingservices.cookcountytreasurer.com/electronictaxbills/viewpropertytaxbill.aspx?billtype=HOE9o+YlPZo%3D&installment=YqDOeLsN+Qo%3D&pin=f%2FsdwN9suvw0ELnAuq98iQ%3D%3D&taxyear=LHRsjdC%2F4po%3D", "MEDIUM"
    ),
    "4004 DENICE|GLENVIEW|IL|60025": (
        "OWNER_HOME_OFFICE", "This is a single-family residence also used as LLC headquarters/legal address; no professional intermediary signal found.",
        "https://www.compass.com/homedetails/4004-Denice-Ct-Glenview-IL-60025/1UYUHY_pid/", "MEDIUM"
    ),
    "4545 W ARMITAGE|CHICAGO|IL|60639": (
        "OWNER_INVESTOR_OFFICE", "Public records connect the Fattah investor portfolio and LLC mailing addresses directly to this location.",
        "https://elementix.com/investors/il/abraham-fattah", "MEDIUM"
    ),
    "4622 N VIRGINIA|CHICAGO|IL|60625": (
        "OWNER_HOME_OFFICE", "The address is an owner-occupied single-family residence; no professional intermediary signal found.",
        "https://www.countyoffice.org/property-record-4622-n-virginia-ave-chicago-il-60625-4a1/", "MEDIUM"
    ),
    "1104 FAIRFIELD|GLENCOE|IL|60022": (
        "OWNER_DEVELOPER_HOME_OFFICE", "Public development filings connect the developer directly to this residential address.",
        "https://d3n9y02raazwpg.cloudfront.net/villageofschaumburg/42a5d210-56b0-11f0-b7f5-005056a89546-0b364dc2-5c07-4547-9bb6-6f6209a9901c-1754579393.pdf", "HIGH"
    ),
    "6409 ALISHIA CIR|LAS VEGAS|NV|89130": (
        "OWNER_HOME_OFFICE", "Cook tax records connect multiple LLC properties to this single-family residential mailing address; no intermediary signal found.",
        "https://www.cookcountytreasurer.com/PDFs/SaleStats/2017AnnualTaxSale/StateRep/5.pdf", "MEDIUM"
    ),
    "32 N DEAN ST 2ND FL|ENGLEWOOD|NJ|07631": (
        "OWNER_INVESTMENT_OFFICE", "Public property-owner filings identify Antheus Capital and affiliated ownership entities at this office.",
        "https://mostateparks.com/sites/mostateparks/files/Windsor%20Hall%20Apts.pdf", "HIGH"
    ),
    "32 N DEAN ST 2ND FLR|ENGLEWOOD|NJ|07631": (
        "OWNER_INVESTMENT_OFFICE", "This floor-format variant is the researched Antheus Capital owner/investment office.",
        "https://mostateparks.com/sites/mostateparks/files/Windsor%20Hall%20Apts.pdf", "HIGH"
    ),
    "32 N DEAN ST 2FL|ENGLEWOOD|NJ|07631": (
        "OWNER_INVESTMENT_OFFICE", "This floor-format variant is the researched Antheus Capital owner/investment office.",
        "https://mostateparks.com/sites/mostateparks/files/Windsor%20Hall%20Apts.pdf", "HIGH"
    ),
    "450 SKOKIE|#604|NORTHBROOK|IL|60062": (
        "OWNER_INVESTMENT_OFFICE", "SEC and municipal ownership disclosures connect issuer managers and property-owning entities directly to this suite.",
        "https://www.sec.gov/Archives/edgar/data/1581240/000158124013000001/xslFormDX06/primary_doc.xml", "HIGH"
    ),
    "450 SKOKIE BLVD 604|NORTHBROOK|IL|60062": (
        "OWNER_INVESTMENT_OFFICE", "This address-format variant is the researched owner/investment office at suite 604.",
        "https://www.sec.gov/Archives/edgar/data/1581240/000158124013000001/xslFormDX06/primary_doc.xml", "HIGH"
    ),
    "111 S WACKER|#4730|CHICAGO|IL|60606": (
        "OWNER_INVESTMENT_OFFICE", "Illinois property-tax appeal records connect a large JVA ownership portfolio directly to this suite; the suite is shared with another financial firm.",
        "https://ptab.illinois.gov/web/Decisions/2018/2018-35245.pdf", "MEDIUM"
    ),
    "111 S WACKER ST 4730|CHICAGO|IL|60606": (
        "OWNER_INVESTMENT_OFFICE", "This address-format variant is the researched JVA owner/investment office at suite 4730.",
        "https://ptab.illinois.gov/web/Decisions/2018/2018-35245.pdf", "MEDIUM"
    ),
    "2234 W NORTH|CHICAGO|IL|60647": (
        "OWNER_DEVELOPER", "City development filings identify LG Development Group and affiliated project entities at this developer address.",
        "https://gisapps.chicago.gov/gisimages/zoning_pds/PD1512.pdf", "HIGH"
    ),
    "2618 EASTWOOD|EVANSTON|IL|60201": (
        "OWNER_HOME_OFFICE", "Public property records identify this as a small residential multifamily address; no professional intermediary signal was found.",
        "https://www.cityofevanston.org/home/showpublisheddocument/88802/638156055226170000", "MEDIUM"
    ),
    "3423 N DRAKE|CHICAGO|IL|60618": (
        "OWNER_INVESTMENT_OFFICE", "City disclosures identify Novak Family Real Estate and controlled project entities directly at this business address.",
        "https://occprodstoragev1.blob.core.usgovcloudapi.net/lsmatterattachmentspublic/81ae66a8-37c5-4360-80f9-5d6a0b2b649c.pdf", "HIGH"
    ),
    "3009 W MONTROSE|CHICAGO|IL|60618": (
        "OWNER_DEVELOPER", "Noah Properties is documented at this address as a licensed builder/developer with its own projects; no third-party service-provider signal was found.",
        "https://www.buildzoom.com/contractor/noah-properties-llc", "MEDIUM"
    ),
    "1250 N PAULINA|CHICAGO|IL|60622": (
        "OWNER_HOME_OFFICE", "Public ownership records connect property-owning LLCs to this residential mailing address; no third-party professional intermediary was identified.",
        "https://greatcities.uic.edu/wp-content/uploads/2020/06/Pilsen-QoL-Plan-May2020-Addendum.pdf", "MEDIUM"
    ),
    "1909 N CLIFTON|CHICAGO|IL|60614": (
        "OWNER_OPERATOR", "Illinois environmental records identify GII LLC as both owner and operator at this address.",
        "https://news.wttw.com/sites/default/files/article/file-attachments/IEPA%205-13-20%20inspection%20report.pdf", "HIGH"
    ),
    "2222 N ELSTON|#100|CHICAGO|IL|60614": (
        "OWNER_DEVELOPER", "Government filings identify Baker Development Corporation and affiliated investment entities at this suite.",
        "https://lobbyist.phoenix.gov/Forms/Registration/e6d9cb41-87a5-4466-bd2b-9784d795a648", "HIGH"
    ),
    "1315 N NORTH BRANCH 2D|CHICAGO|IL|60642": (
        "OWNER_INVESTMENT_OFFICE", "R2's published portfolio and company materials connect its ownership and investment platform directly to this address.",
        "https://r2.me/portfolio/", "HIGH"
    ),
    "333 W NORTH|#415|CHICAGO|IL|60610": (
        "OWNER_INVESTMENT_OFFICE", "Tax records connect multiple property-owning LLCs to this suite; the registered-agent evidence is an individual affiliated with an entity rather than a third-party agent service.",
        "https://augrented.com/chicago/20034140250000-438-e-45th-pl", "MEDIUM"
    ),
    "8060 LAWNDALE|SKOKIE|IL|60076": (
        "OWNER_OPERATOR", "Government records identify LLC sellers, current property owners and the affiliated real-estate/construction operation at this address.",
        "https://files.illinoiscomptroller.gov/LocGovTIF/FY2025/01616532/25TIF01616532Arlington_Higgins_2.pdf", "HIGH"
    ),
    "1038 N ASHLAND|#100|CHICAGO|IL|60622": (
        "OWNER_OPERATOR", "Honore Holdings states that it owns a substantial portfolio and conducts hands-on management from this exact office.",
        "https://www.honoreholdings.com/about", "HIGH"
    ),
    "2625 BUTTERFIELD|OAK BROOK|IL|60523": (
        "OWNER_INVESTMENT_OFFICE", "Government ownership records connect multiple CHP industrial property-owning entities directly to this office.",
        "https://d3n9y02raazwpg.cloudfront.net/northbrook-il/8b4ca298-74cd-11ee-b4aa-0050569183fa-d638ec48-0581-42d3-a7cb-5eb59bc78d4c-1728075689.pdf", "HIGH"
    ),
    "110 W GOLF|SCHAUMBURG|IL|60195": (
        "OWNER_OPERATOR", "Government property records connect owner entities to this address, which is an operating Napleton dealership rather than a professional intermediary office.",
        "https://www.warrenville.il.us/DocumentCenter/View/21218/F-7-Retail-Space-Inventory-January-2023", "MEDIUM"
    ),
    "1200 RIVER AVE BLDG 4|LAKEWOOD|NJ|08701": (
        "OWNER_INVESTMENT_OFFICE", "SEC filings and the firm's own site identify this as Strategic Properties of North America's principal investment office.",
        "https://www.sec.gov/Archives/edgar/data/1810631/000181063120000001/xslFormDX01/primary_doc.xml", "HIGH"
    ),
    "ATTN PROPERTY TAX DEPARTMENT 23975 PARK SORRENTO|#300|CALABASAS|CA|91302": (
        "OWNER_CORPORATE_TAX_OFFICE", "Official assessor records identify the address as the property-tax department for AMH owner entities, not an outside tax consultant.",
        "https://paopropertysearch.coj.net/Basic/Detail.aspx?RE=0160577330", "HIGH"
    ),
    "2035 W GIDDINGS|CHICAGO|IL|60625": (
        "OWNER_HOME_OFFICE", "Public records identify a single-family home used by affiliated owner, construction and in-house management entities; no third-party intermediary was established.",
        "https://nrschicago.com/wp-content/uploads/2025/06/V40N25.pdf", "MEDIUM"
    ),
    "3050 FINLEY|#300D|DOWNERS GROV|IL|60515": (
        "OWNER_OPERATOR", "Janko Hospitality publishes this exact suite as its headquarters for its hotel ownership and operating platform.",
        "https://www.jankohospitality.com/privacy-policy", "HIGH"
    ),
    "9450 W BRYN MAWR|#750|ROSEMONT|IL|60018": (
        "OWNER_INVESTMENT_OFFICE", "Public entity records connect Brennan Investment Group and its property-owning entities to this exact suite.",
        "https://lei.bloomberg.com/leis/view/549300I46YGHOXAXH092", "MEDIUM"
    ),
    "600 W VAN BUREN|#1000|CHICAGO|IL|60607": (
        "OWNER_DEVELOPER", "Government records identify Blue Star Properties and affiliated LLCs as property owners represented from this exact suite.",
        "https://cityofevanston.prod.govaccess.org/home/showpublisheddocument/87969/638122474021570000", "HIGH"
    ),
    "853 N ELSTON|CHICAGO|IL|60642": (
        "OWNER_DEVELOPER", "Government filings identify JDI Realty and affiliated applicants as owners at this address.",
        "https://hampshirelive.muniweb.com/media/xe2jcvpz/vbm-agenda-packet_080625.pdf", "HIGH"
    ),
}


STREET_SUFFIXES = {
    "ST", "STREET", "AVE", "AV", "AVENUE", "RD", "ROAD", "DR", "DRIVE", "BLVD", "BOULEVARD",
    "PKWY", "PARKWAY", "CT", "COURT", "LN", "LANE", "PL", "PLACE", "TER", "TERRACE", "HWY",
}
UNIT_WORDS = {"STE", "SUITE", "UNIT", "APT", "APARTMENT", "FL", "FLOOR", "RM", "ROOM", "#"}
DIRECT_SERVICE_RE = re.compile(
    r"\b(LAW OFFICE|LAW FIRM|ATTORNEY|LEGAL SERVICES?|CERTIFIED PUBLIC ACCOUNT|\bCPA\b|ACCOUNTING|"
    r"REGISTERED AGENT|CORPORATE SERVICES?|INCORPORAT(?:E|ION|ING)|FILING SERVICES?|TITLE COMPANY)\b",
    re.I,
)


def clean(value: str) -> str:
    value = (value or "").upper().replace(".", " ").replace(",", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_street(value: str) -> tuple[str, str]:
    value = clean(value).replace("LA SALLE", "LASALLE")
    value = re.sub(r"(?<=\w)#(?=\w)", " #", value)
    value = re.sub(r"\b(SUITE|STE|UNIT|APT|APARTMENT|FLOOR|FL|ROOM|RM)(?=\s|#|\d)\s*#?\s*([A-Z0-9-]+)\b", r" #\2", value)
    value = re.sub(r"#\s*([A-Z0-9-]+)", r" #\1", value)
    tokens = value.split()
    unit = ""
    for idx, token in enumerate(tokens):
        if token.startswith("#"):
            unit = token
            tokens = tokens[:idx]
            break
        if token in UNIT_WORDS and idx + 1 < len(tokens):
            unit = "#" + tokens[idx + 1].lstrip("#")
            tokens = tokens[:idx]
            break
    while tokens and tokens[-1] in STREET_SUFFIXES:
        tokens.pop()
    return " ".join(tokens), unit


def screening_key(row: dict[str, str]) -> str:
    address = clean(row["mail_address"])
    city, state, zipcode = clean(row["mail_city"]), clean(row["mail_state"]), clean(row["mail_zip"])
    if address.startswith("PO BOX") or address.startswith("P O BOX"):
        address = re.sub(r"^P\s*O\s*BOX\s*", "PO BOX ", address)
        return f"{address}|{city}|{state}|{zipcode}"
    base, unit = parse_street(address)
    return "|".join(part for part in (base, unit, city, state, zipcode) if part != "")


def split_values(value: str) -> set[str]:
    return {part.strip() for part in (value or "").split("|") if part.strip()}


def is_po_box(address: str) -> bool:
    return bool(re.search(r"\bP\s*\.?\s*O\s*\.?\s+BOX\b", address, re.I))


def has_unit(address: str) -> bool:
    return bool(re.search(r"(?:#\s*[A-Z0-9]|\b(?:STE|SUITE|UNIT|APT|FL|FLOOR|RM|ROOM|PMB)\b)", address, re.I))


def classify(row: dict[str, str]) -> dict[str, str]:
    key = row["screening_address_key_v2"]
    llc_names = row["llc_names"]
    if key in KNOWN_SERVICE_ADDRESSES:
        category, summary, url, confidence = KNOWN_SERVICE_ADDRESSES[key]
        return {
            "screening_status": "SUPPRESS_SERVICE_PROVIDER",
            "screening_reason_code": "CONFIRMED_SERVICE_PROVIDER_ADDRESS",
            "provider_category": category,
            "evidence_summary": summary,
            "evidence_url": url,
            "evidence_confidence": confidence,
        }
    if key in KNOWN_OWNER_OPERATOR_ADDRESSES:
        category, summary, url, confidence = KNOWN_OWNER_OPERATOR_ADDRESSES[key]
        return {
            "screening_status": "PASS_SERVICE_SCREEN",
            "screening_reason_code": "RESEARCH_CONFIRMED_OWNER_OPERATOR",
            "provider_category": category,
            "evidence_summary": summary,
            "evidence_url": url,
            "evidence_confidence": confidence,
        }
    match = DIRECT_SERVICE_RE.search(llc_names)
    if match:
        return {
            "screening_status": "SUPPRESS_SERVICE_PROVIDER",
            "screening_reason_code": "DIRECT_PROFESSIONAL_NAME_SIGNAL",
            "provider_category": "LAW_ACCOUNTING_REGISTERED_AGENT_OR_FILING_SERVICE",
            "evidence_summary": f"LLC-name list contains direct professional-service term: {match.group(0).upper()}.",
            "evidence_url": "",
            "evidence_confidence": "MEDIUM",
        }
    reasons = []
    if not row["mail_zip"].strip():
        reasons.append("MISSING_ZIP")
    if is_po_box(row["mail_address"]):
        reasons.append("PO_BOX_OR_LOCKBOX")
    if has_unit(row["mail_address"]):
        reasons.append("SUITE_UNIT_OR_MAILBOX")
    if int(row["distinct_llc_count"]) >= 5:
        reasons.append("HIGH_ADDRESS_COLLISION_5_PLUS_LLCS")
    if reasons:
        return {
            "screening_status": "MANUAL_REVIEW",
            "screening_reason_code": ";".join(reasons),
            "provider_category": "UNRESOLVED",
            "evidence_summary": "Address needs ownership-vs-service-provider review before campaign use.",
            "evidence_url": "",
            "evidence_confidence": "NOT_CLASSIFIED",
        }
    return {
        "screening_status": "PASS_SERVICE_SCREEN",
        "screening_reason_code": "LOW_COLLISION_NO_SERVICE_SIGNAL",
        "provider_category": "NO_SERVICE_PROVIDER_SIGNAL_FOUND",
        "evidence_summary": "Two to four LLCs share a simple street address; no deterministic service-provider signal found.",
        "evidence_url": "",
        "evidence_confidence": "PRELIMINARY",
    }


def regroup(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[screening_key(row)].append(row)
    output = []
    for key, members in groups.items():
        llcs, parcels, counties, original_keys = set(), set(), set(), set()
        for member in members:
            llcs.update(split_values(member["llc_names"]))
            parcels.update(split_values(member["parcel_keys"]))
            counties.update(split_values(member["counties"]))
            original_keys.add(member["owner_mailing_address_key"])
        exemplar = max(members, key=lambda r: (len(r["mail_address"]), len(r["mail_zip"])))
        row = {
            "screening_address_key_v2": key,
            "mail_address": exemplar["mail_address"],
            "mail_city": exemplar["mail_city"],
            "mail_state": exemplar["mail_state"],
            "mail_zip": exemplar["mail_zip"],
            "distinct_llc_count": str(len(llcs)),
            "property_count": str(len(parcels)),
            "county_count": str(len(counties)),
            "counties": " | ".join(sorted(counties)),
            "llc_names": " | ".join(sorted(llcs)),
            "parcel_keys": " | ".join(sorted(parcels)),
            "source_cluster_count": str(len(members)),
            "source_address_keys": " | ".join(sorted(original_keys)),
            "coverage_status": "PARTIAL_MSA_COOK_AND_KENDALL_ONLY",
            "screened_as_of_date": AS_OF_DATE,
            "usps_cass_dpv_status": "NOT_RUN",
            "mailing_status": "NOT_MAIL_READY_POSTAL_VALIDATION_REQUIRED",
        }
        row.update(classify(row))
        output.append(row)
    return sorted(output, key=lambda r: (-int(r["distinct_llc_count"]), r["screening_address_key_v2"]))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    with INPUT.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    screened = regroup(rows)
    fields = [
        "screening_address_key_v2", "mail_address", "mail_city", "mail_state", "mail_zip",
        "distinct_llc_count", "property_count", "county_count", "counties", "llc_names", "parcel_keys",
        "screening_status", "screening_reason_code", "provider_category", "evidence_summary", "evidence_url",
        "evidence_confidence", "source_cluster_count", "source_address_keys", "coverage_status",
        "screened_as_of_date", "usps_cass_dpv_status", "mailing_status",
    ]
    write_csv(ALL_OUTPUT, screened, fields)
    targets = {
        "PASS_SERVICE_SCREEN": FINAL_DIR / "chicago_msa_partial_PASS_SERVICE_SCREEN_PREPOSTAL_20260828.csv",
        "SUPPRESS_SERVICE_PROVIDER": FINAL_DIR / "chicago_msa_partial_SUPPRESS_SERVICE_PROVIDERS_20260828.csv",
        "MANUAL_REVIEW": FINAL_DIR / "chicago_msa_partial_MANUAL_REVIEW_20260828.csv",
    }
    for status, path in targets.items():
        write_csv(path, [row for row in screened if row["screening_status"] == status], fields)
    counts = {status: sum(row["screening_status"] == status for row in screened) for status in targets}
    print(f"input_clusters={len(rows)} regrouped_clusters={len(screened)} counts={counts}")


if __name__ == "__main__":
    main()
