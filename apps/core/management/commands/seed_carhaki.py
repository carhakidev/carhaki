"""
Management command: seed_carhaki
Populates the database with realistic Ugandan test data.
"""
import uuid
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed the database with realistic CarHaki test data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding CarHaki database...')
        self._seed_site_config()
        self._seed_faqs()
        self._seed_recalls()
        users = self._seed_users()
        dealers = self._seed_dealers(users)
        reports = self._seed_reports(users)
        self._seed_orders(users, reports)
        self._seed_contacts()
        self._seed_dealer_applications()
        self.stdout.write(self.style.SUCCESS('Database seeded successfully.'))

    def _seed_site_config(self):
        from apps.core.models import SiteConfig
        config = SiteConfig.get_solo()
        config.usd_to_ugx_rate = 3720
        config.basic_report_ugx = 35000
        config.full_report_ugx = 75000
        config.dealer_pack_10_ugx = 600000
        config.save()
        self.stdout.write('  Site config updated.')

    def _seed_faqs(self):
        from apps.core.models import FAQ
        if FAQ.objects.exists():
            self.stdout.write('  FAQs already exist, skipping.')
            return

        faqs_data = [
            # About the Reports
            (FAQ.ABOUT_REPORTS, 'What is a vehicle history report?',
             'A vehicle history report is a document that summarises the recorded history of a specific vehicle based on official government and insurance databases. For cars from the USA, it shows title records, accident history, odometer readings, and recall status. For cars from Japan, it shows auction history, inspection grades, and MLIT registration records. CarHaki compiles this data into a clear, easy-to-read report so you can make an informed decision before buying.', 1),

            (FAQ.ABOUT_REPORTS, 'What information does a CarHaki Full Report contain?',
             'A Full Report includes: overall vehicle grade (A to F), AI-generated plain-English summary, title history with all recorded brands (salvage, rebuilt, not actual mileage), odometer history chart, accident and damage records, theft records, open safety recalls, market value estimate, Uganda URA import eligibility check, and for Japan vehicles: auction grade, auction records, and Shaken validity dates. A Basic Report includes vehicle specifications, title status summary, and recall check.', 2),

            (FAQ.ABOUT_REPORTS, 'How is CarHaki different from just trusting the seller?',
             'A seller can tell you anything about a car. CarHaki accesses official government databases that record what actually happened to the vehicle, regardless of what the seller says. If a car was in a flood, declared a total loss, had its mileage rolled back, or was reported stolen, those events are recorded in databases that the seller cannot alter. The report shows you the documented truth.', 3),

            (FAQ.ABOUT_REPORTS, 'Can a report guarantee a car is in good condition?',
             'No report can guarantee a car is in perfect mechanical condition. CarHaki reports show the recorded history of a vehicle, but not all damage is reported to databases. We always recommend getting an independent mechanical inspection from a qualified mechanic in addition to a CarHaki report.', 4),

            (FAQ.ABOUT_REPORTS, 'What does a salvage title mean for a car being sold in Uganda?',
             'A salvage title means an insurance company declared the vehicle a total loss, typically after a serious accident, flood, or theft. Salvage-titled vehicles can be cheaper to buy but may have structural weaknesses affecting safety and resale value. Banks in Uganda typically do not finance salvage-titled vehicles. CarHaki flags salvage records prominently in reports.', 5),

            (FAQ.ABOUT_REPORTS, 'What does a rebuilt title mean and is it safe to buy?',
             'A rebuilt title means the vehicle was previously a salvage vehicle that was repaired and passed a state inspection in its country of origin. Whether it is safe depends on the quality of the repairs. CarHaki flags rebuilt titles clearly. We strongly advise a thorough independent mechanical inspection for any rebuilt title vehicle.', 6),

            (FAQ.ABOUT_REPORTS, 'What is an auction sheet and why does it matter for Japanese imports?',
             'An auction sheet is a condition report produced by independent inspectors at Japanese car auctions. It records every dent, scratch, rust spot, and mechanical issue along with an overall grade (S to 1, with R and RA indicating repaired damage). The auction sheet is highly reliable because it was produced independently before the car left Japan.', 7),

            # Searching
            (FAQ.SEARCHING, 'What is a VIN number and where do I find it on the car?',
             'A VIN (Vehicle Identification Number) is a 17-character alphanumeric code that uniquely identifies every vehicle made for the American market. You can find it on a metal plate visible through the windshield on the driver side dashboard, on a sticker inside the driver door frame, on the engine block, and on the vehicle registration documents. The characters I, O, and Q are never used in a valid VIN.', 1),

            (FAQ.SEARCHING, 'What is a chassis number and how is it different from a VIN?',
             'A chassis number is the identifier used for Japanese vehicles. Unlike the 17-character American VIN, Japanese chassis numbers are shorter (8 to 14 characters) and follow the pattern of a model code followed by a serial number, such as ZZT240-987654. Chassis numbers are stamped on the firewall between the engine and the cabin and appear on the vehicle registration certificate.', 2),

            (FAQ.SEARCHING, 'The car has a 9-character number, not 17. Is this still searchable?',
             'A number shorter than 17 characters is most likely a Japanese chassis number, not an American VIN. Select Japan as the country of origin when searching. If the number is between 8 and 14 characters and alphanumeric, CarHaki will attempt a Japan chassis search.', 3),

            (FAQ.SEARCHING, 'I searched but got no results. What does this mean?',
             'No results can mean several things: the vehicle was manufactured before electronic records were widely kept; the identifier was not correctly transcribed; the vehicle is a grey-market import not in US or Japanese databases; or the database simply does not have records for that specific vehicle. No results do not necessarily mean the vehicle has a bad history. Contact us at support@carhaki.ug for assistance.', 4),

            (FAQ.SEARCHING, 'Can I search for any car or only cars from Japan and the USA?',
             'Currently CarHaki supports vehicles from Japan (using the chassis number) and the United States (using the 17-digit VIN). These two countries account for the majority of used vehicle imports into Uganda. We are working on adding support for vehicles from the United Kingdom and Singapore.', 5),

            # Payments
            (FAQ.PAYMENTS, 'What payment methods does CarHaki accept?',
             'CarHaki accepts MTN Mobile Money, Airtel Money, and Visa or Mastercard payments through Flutterwave. All prices are in Uganda Shillings (UGX). MTN and Airtel Mobile Money are available for all Ugandan phone numbers. Card payments accept both Ugandan and international cards.', 1),

            (FAQ.PAYMENTS, 'How do I pay using MTN Mobile Money?',
             'On the checkout page, select MTN Mobile Money, enter your MTN phone number in 256XXXXXXXXX format, and click Pay. You will receive a payment prompt on your phone. Enter your Mobile Money PIN to confirm. Report generation begins immediately after payment is confirmed.', 2),

            (FAQ.PAYMENTS, 'How do I pay using Airtel Money?',
             'On the checkout page, select Airtel Money, enter your Airtel phone number in 256XXXXXXXXX format, and click Pay. You will receive a payment prompt from Airtel. Enter your PIN to confirm. Report generation begins immediately after payment is confirmed.', 3),

            (FAQ.PAYMENTS, 'I paid but did not receive my report. What should I do?',
             'Report generation usually takes 1 to 3 minutes after payment is confirmed. If more than 10 minutes have passed and your report is not in your dashboard, contact us at support@carhaki.ug with your transaction reference number. We will investigate and either deliver your report or process a refund.', 4),

            (FAQ.PAYMENTS, 'Are reports refundable?',
             'Once a report has been successfully generated, it is non-refundable because the cost of retrieving data from third-party providers has already been incurred. If a report completely failed to generate after payment was confirmed, we will generate it again or issue a full refund. Contact support@carhaki.ug within 7 days with your transaction reference number.', 5),

            (FAQ.PAYMENTS, 'Can I buy multiple reports at a discount?',
             'Yes. Dealer account holders can purchase bulk credit packs at reduced rates. A Starter Pack of 10 reports costs UGX 600,000 (saving UGX 150,000 compared to buying individually). Larger packs of 25, 50, and 100 reports offer even greater savings. See the Dealer Programme page for full pricing details.', 6),

            # Understanding Results
            (FAQ.UNDERSTANDING, 'What do the letter grades A through F mean?',
             'CarHaki uses a penalty scoring system starting at 100 points. Points are deducted for each negative finding: salvage title (-40), total loss (-35), flood damage (-35), not actual mileage (-30), rebuilt title (-20), major accident (-20 each), theft (-20), open recall (-10 each), and minor accident (-8). The final score determines the grade: A (90-100, Excellent), B (75-89, Good), C (60-74, Acceptable), D (45-59, Concerning), E (20-44, Poor), F (0-19, Critical Risk).', 1),

            (FAQ.UNDERSTANDING, 'The report shows the car was sold as salvage. Should I still buy it?',
             'A salvage record is a serious concern but not an automatic disqualification. The key questions are: Was it repaired and does it now have a rebuilt title? What was the nature of the damage? What is the quality of the repair? CarHaki always recommends a thorough independent mechanical inspection for any salvage-history vehicle.', 2),

            (FAQ.UNDERSTANDING, 'The mileage in the report does not match what the seller told me. Is this fraud?',
             'A significant discrepancy between recorded mileage and the stated mileage is a serious red flag. If recorded readings are higher than the seller claim, the odometer may have been tampered with. This is illegal in both the USA and Japan. CarHaki flags odometer discrepancies clearly in reports. We strongly advise against purchasing a vehicle with suspected odometer fraud.', 3),

            (FAQ.UNDERSTANDING, 'There are open recalls on the vehicle. What should I do?',
             'An open recall means a safety defect has been identified by the manufacturer and not yet repaired. For a vehicle already imported to Uganda, contact the manufacturer regional office to enquire about local remedy options, or have a qualified mechanic assess the severity and advise on alternatives. Read the recall summary in the report carefully before proceeding with a purchase.', 4),
        ]

        for category, question, answer, order in faqs_data:
            FAQ.objects.create(
                category=category,
                question=question,
                answer=answer,
                order=order,
                is_active=True,
            )
        self.stdout.write(f'  Created {len(faqs_data)} FAQ entries.')

    def _seed_recalls(self):
        from apps.vehicles.models import RecallAlert
        if RecallAlert.objects.exists():
            self.stdout.write('  Recalls already exist, skipping.')
            return

        recalls = [
            {
                'vin': '5TDYK3DC8DS290235',
                'recall_number': '13V014000',
                'component': 'Air Bags: Frontal: Sensor/Control Module',
                'summary': 'Toyota is recalling certain model year 2011-2013 Sienna vehicles. The occupant detection system may have an incorrect setting, causing the passenger frontal air bag to be suppressed in certain occupant conditions.',
                'remedy': 'Toyota dealers will reprogram the occupant classification system software, free of charge.',
                'issued_date': date(2013, 2, 5),
                'is_open': False,
                'source': RecallAlert.NHTSA,
            },
            {
                'vin': '5TDYK3DC8DS290235',
                'recall_number': '16V858000',
                'component': 'Structure: Body: Door: Power Sliding Door',
                'summary': 'Toyota is recalling certain 2011-2016 Sienna vehicles. The power sliding door may stop unexpectedly or reverse direction when closing due to a software issue.',
                'remedy': 'Toyota dealers will update the power sliding door ECU software, free of charge.',
                'issued_date': date(2016, 12, 1),
                'is_open': False,
                'source': RecallAlert.NHTSA,
            },
            {
                'vin': '5TDYK3DC8DS290235',
                'recall_number': '19V005000',
                'component': 'Air Bags: Frontal: Passenger Side Inflator Module',
                'summary': 'This recall addresses Takata airbag inflators which may explode due to moisture infiltration. An inflator explosion may result in sharp metal fragments striking the driver or other occupants, potentially resulting in serious injury or death.',
                'remedy': 'Toyota dealers will replace the passenger-side frontal airbag inflator, free of charge. Part availability may require scheduling.',
                'issued_date': date(2019, 1, 10),
                'is_open': True,
                'source': RecallAlert.NHTSA,
            },
            {
                'vin': '5TDYK3DC8DS290235',
                'recall_number': '18V024000',
                'component': 'Air Bags: Frontal: Passenger Side Inflator Module (Takata Zone A)',
                'summary': 'Takata Zone A recall. The affected air bag inflators may rupture, sending metal fragments toward vehicle occupants. This is a serious safety defect that requires immediate attention.',
                'remedy': 'Replace the airbag inflator at an authorised Toyota dealer at no charge to the owner.',
                'issued_date': date(2018, 1, 11),
                'is_open': True,
                'source': RecallAlert.NHTSA,
            },
            {
                'vin': '5TDYK3DC8DS290235',
                'recall_number': '19V741000',
                'component': 'Air Bags: Frontal: Driver Side Inflator Module',
                'summary': 'Driver side Takata inflator recall. Affected inflators may rupture due to moisture and cause metal fragmentation injury. All affected vehicles must be inspected and repaired.',
                'remedy': 'Toyota dealers will replace the driver-side frontal airbag inflator free of charge.',
                'issued_date': date(2019, 10, 14),
                'is_open': True,
                'source': RecallAlert.NHTSA,
            },
        ]

        for data in recalls:
            try:
                RecallAlert.objects.create(**data)
            except Exception:
                pass
        self.stdout.write(f'  Created {len(recalls)} recall records.')

    def _seed_users(self):
        from apps.accounts.models import CustomUser
        users_data = [
            {'first_name': 'David', 'last_name': 'Ssekandi', 'email': 'david.ssekandi@gmail.com', 'phone_number': '256772345678', 'country': 'Uganda'},
            {'first_name': 'Grace', 'last_name': 'Nakato', 'email': 'grace.nakato@yahoo.com', 'phone_number': '256756789012', 'country': 'Uganda'},
            {'first_name': 'Brian', 'last_name': 'Tumwesigye', 'email': 'brian.tumwesigye@carhaki.ug', 'phone_number': '256704567890', 'country': 'Uganda'},
            {'first_name': 'Sarah', 'last_name': 'Aheebwa', 'email': 'sarahaheebwa@hotmail.com', 'phone_number': '256750123456', 'country': 'Uganda'},
            {'first_name': 'Robert', 'last_name': 'Ochieng', 'email': 'robert.ochieng@gmail.com', 'phone_number': '256712345678', 'country': 'Uganda'},
        ]

        created_users = []
        for data in users_data:
            user, created = CustomUser.objects.get_or_create(
                email=data['email'],
                defaults={
                    'username': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone_number': data['phone_number'],
                    'country': data['country'],
                    'account_type': CustomUser.INDIVIDUAL,
                    'is_verified': True,
                }
            )
            if created:
                user.set_password('TestPass2024!')
                user.save()
            created_users.append(user)

        self.stdout.write(f'  Created/found {len(created_users)} regular users.')
        return created_users

    def _seed_dealers(self, users):
        from apps.accounts.models import CustomUser, DealerProfile
        dealers_data = [
            {'business_name': 'Kampala Auto Mart', 'email': 'info@kampalautomart.ug', 'phone': '256700111222', 'user_email': 'dealer1@kampalautomart.ug', 'first_name': 'Patrick', 'last_name': 'Mugisha', 'credits': 35},
            {'business_name': 'Pearl Motors Uganda', 'email': 'sales@pearlmotors.ug', 'phone': '256700222333', 'user_email': 'dealer2@pearlmotors.ug', 'first_name': 'Jane', 'last_name': 'Nakyobe', 'credits': 22},
            {'business_name': 'Nile Valley Motors', 'email': 'info@nilevalleymotors.ug', 'phone': '256700333444', 'user_email': 'dealer3@nilevalleymotors.ug', 'first_name': 'Steven', 'last_name': 'Tukwasibwe', 'credits': 48},
            {'business_name': 'Safari Auto Dealers', 'email': 'sales@safariauto.ug', 'phone': '256700444555', 'user_email': 'dealer4@safariauto.ug', 'first_name': 'Robert', 'last_name': 'Katumba', 'credits': 15},
            {'business_name': 'Buganda Road Motors', 'email': 'info@bugandaroadmotors.ug', 'phone': '256700555666', 'user_email': 'dealer5@bugandaroadmotors.ug', 'first_name': 'Annet', 'last_name': 'Namusoke', 'credits': 30},
        ]

        for data in dealers_data:
            user, created = CustomUser.objects.get_or_create(
                email=data['user_email'],
                defaults={
                    'username': data['user_email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'phone_number': data['phone'],
                    'country': 'Uganda',
                    'account_type': CustomUser.DEALER,
                    'is_verified': True,
                }
            )
            if created:
                user.set_password('DealerPass2024!')
                user.save()

            DealerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'business_name': data['business_name'],
                    'contact_email': data['email'],
                    'contact_phone': data['phone'],
                    'credit_balance': data['credits'],
                    'is_approved': True,
                }
            )

        self.stdout.write(f'  Created/found {len(dealers_data)} dealer accounts.')
        return dealers_data

    def _seed_reports(self, users):
        from apps.vehicles.models import VehicleSearch, VehicleReport

        reports_data = [
            {
                'identifier': 'ACU301234567',
                'identifier_type': VehicleSearch.CHASSIS,
                'source_country': VehicleSearch.JAPAN,
                'report_type': VehicleReport.FULL,
                'overall_grade': 'B',
                'risk_score': 80,
                'ai_summary': 'This Toyota Harrier is in good condition based on available records. The auction grade of 4 indicates minor cosmetic imperfections but no significant mechanical issues. The vehicle has had two owners in Japan and the mileage appears consistent with its age. The Shaken (vehicle inspection) certificate is valid. There are no recorded accidents, theft records, or open recalls. This vehicle appears to be a reasonable purchase, but we always recommend an independent mechanical inspection before completing the transaction.',
                'processed_data': {
                    'meta': {'source_country': 'JAPAN', 'identifier': 'ACU301234567', 'identifier_type': 'CHASSIS', 'report_type': 'FULL'},
                    'vehicle': {'make': 'Toyota', 'model': 'Harrier', 'year': 2008, 'engine': '2.4L 4-Cylinder', 'body_type': 'SUV', 'fuel_type': 'Petrol'},
                    'brands': [],
                    'accidents': [],
                    'theft': [],
                    'recalls': [],
                    'auction_grade': '4',
                    'auction_history': [{'auction_house': 'USS Tokyo', 'date': '2018-03-15', 'grade': '4', 'odometer_km': 98000}],
                    'odometer_records': [{'date': '2018-03-15', 'reading': 98000, 'unit': 'km'}],
                    'uganda_eligibility': {'eligible': True, 'vehicle_age_years': 17, 'max_allowed_years': 15, 'note': 'Exceeds 15-year URA limit as of 2025'},
                    'risk_score': 80, 'overall_grade': 'B',
                },
            },
            {
                'identifier': '1HGCM82633A004352',
                'identifier_type': VehicleSearch.VIN,
                'source_country': VehicleSearch.USA,
                'report_type': VehicleReport.FULL,
                'overall_grade': 'A',
                'risk_score': 95,
                'ai_summary': 'This Toyota Corolla has a clean history based on available records. There are no title brands, no recorded accidents, and no theft records. The odometer readings are consistent and suggest the vehicle has been driven approximately 13,000 miles per year, which is close to the US national average. There are no open safety recalls. This vehicle appears to be a reasonable purchase, but we always recommend an independent mechanical inspection before completing the transaction.',
                'processed_data': {
                    'meta': {'source_country': 'USA', 'identifier': '1HGCM82633A004352', 'identifier_type': 'VIN', 'report_type': 'FULL'},
                    'vehicle': {'make': 'Honda', 'model': 'Accord', 'year': 2012, 'engine': '2.4L 4-Cylinder', 'body_type': 'Sedan', 'fuel_type': 'Gasoline', 'transmission': '5-Speed Automatic'},
                    'brands': [],
                    'accidents': [],
                    'theft': [],
                    'recalls': [],
                    'odometer_records': [{'date': '2014-06-10', 'reading': 32000, 'unit': 'miles'}, {'date': '2019-09-22', 'reading': 89000, 'unit': 'miles'}],
                    'title_history': [{'state': 'Texas', 'date': '2012-08-01', 'odometer': 0, 'brand': None}],
                    'uganda_eligibility': {'eligible': True, 'vehicle_age_years': 13, 'max_allowed_years': 15, 'note': 'Within the 15-year URA import limit'},
                    'risk_score': 95, 'overall_grade': 'A',
                },
            },
            {
                'identifier': '5TDYK3DC8DS290235',
                'identifier_type': VehicleSearch.VIN,
                'source_country': VehicleSearch.USA,
                'report_type': VehicleReport.FULL,
                'overall_grade': 'F',
                'risk_score': 5,
                'ai_summary': 'This Toyota Sienna has a seriously concerning history and should be approached with extreme caution. The vehicle was declared a total loss by an insurance company and was subsequently rebuilt, receiving both a salvage and rebuilt title brand. A major front-end collision was recorded, during which the airbags deployed. The vehicle has three open Takata airbag safety recalls that have never been repaired. Takata airbag recalls are among the most serious safety recalls ever issued in the United States, as the inflators have been known to rupture and send metal fragments toward occupants, resulting in fatalities. We strongly advise against purchasing this vehicle without full disclosure from the seller, expert evaluation of all repair work, and resolution of all outstanding safety recalls.',
                'processed_data': {
                    'meta': {'source_country': 'USA', 'identifier': '5TDYK3DC8DS290235', 'identifier_type': 'VIN', 'report_type': 'FULL'},
                    'vehicle': {'make': 'Toyota', 'model': 'Sienna', 'year': 2013, 'trim': 'XLE', 'engine': '3.5L V6', 'body_type': 'Van', 'fuel_type': 'Gasoline', 'drive_type': 'FWD'},
                    'brands': ['SALVAGE', 'REBUILT'],
                    'total_loss': True,
                    'accidents': [{'date': '2017-08-14', 'severity': 'MAJOR', 'airbags_deployed': True, 'damage_zones': ['FRONT', 'LEFT_FRONT'], 'description': 'Front-end collision, airbags deployed'}],
                    'theft': [],
                    'recalls': [
                        {'recall_number': '19V005000', 'component': 'Air Bags: Frontal: Passenger Side Inflator Module', 'summary': 'Takata airbag inflator may rupture', 'is_open': True},
                        {'recall_number': '18V024000', 'component': 'Air Bags: Frontal: Passenger Side Inflator Module (Zone A)', 'summary': 'Takata Zone A recall', 'is_open': True},
                        {'recall_number': '19V741000', 'component': 'Air Bags: Frontal: Driver Side Inflator Module', 'summary': 'Takata driver side recall', 'is_open': True},
                    ],
                    'odometer_records': [{'date': '2013-11-05', 'reading': 0, 'unit': 'miles'}, {'date': '2019-03-20', 'reading': 87234, 'unit': 'miles'}],
                    'title_history': [
                        {'state': 'California', 'date': '2013-06-15', 'odometer': 0, 'brand': None},
                        {'state': 'Utah', 'date': '2019-03-20', 'odometer': 87234, 'brand': 'REBUILT'},
                    ],
                    'uganda_eligibility': {'eligible': True, 'vehicle_age_years': 12, 'max_allowed_years': 15, 'note': 'Within the 15-year URA import limit'},
                    'risk_score': 5, 'overall_grade': 'F',
                },
            },
            {
                'identifier': 'GD14521033',
                'identifier_type': VehicleSearch.CHASSIS,
                'source_country': VehicleSearch.JAPAN,
                'report_type': VehicleReport.FULL,
                'overall_grade': 'F',
                'risk_score': 10,
                'ai_summary': 'This Honda Fit has a very concerning history. The auction sheet recorded a grade of R, indicating the vehicle was involved in a major accident and was repaired. Flood damage is strongly indicated by the auction inspection notes. The combination of major structural repair and potential flood damage makes this vehicle high risk. We strongly advise against purchasing this vehicle without full disclosure from the seller and expert evaluation of all repair work.',
                'processed_data': {
                    'meta': {'source_country': 'JAPAN', 'identifier': 'GD14521033', 'identifier_type': 'CHASSIS', 'report_type': 'FULL'},
                    'vehicle': {'make': 'Honda', 'model': 'Fit', 'year': 2010, 'engine': '1.3L 4-Cylinder', 'body_type': 'Hatchback', 'fuel_type': 'Petrol'},
                    'brands': ['FLOOD DAMAGE', 'REPAIRED MAJOR DAMAGE'],
                    'accidents': [{'date': '2016-05-20', 'severity': 'MAJOR', 'airbags_deployed': True, 'damage_zones': ['FRONT', 'ROOF'], 'description': 'Major structural damage'}],
                    'theft': [],
                    'recalls': [],
                    'auction_grade': 'R',
                    'auction_history': [{'auction_house': 'TAA Osaka', 'date': '2019-07-10', 'grade': 'R', 'odometer_km': 76000, 'notes': 'Major repair. Water damage noted on interior panels.'}],
                    'odometer_records': [{'date': '2019-07-10', 'reading': 76000, 'unit': 'km'}],
                    'uganda_eligibility': {'eligible': True, 'vehicle_age_years': 15, 'max_allowed_years': 15, 'note': 'At the 15-year URA limit - borderline eligibility'},
                    'risk_score': 10, 'overall_grade': 'F',
                },
            },
            {
                'identifier': 'SG5098765',
                'identifier_type': VehicleSearch.CHASSIS,
                'source_country': VehicleSearch.JAPAN,
                'report_type': VehicleReport.FULL,
                'overall_grade': 'A',
                'risk_score': 92,
                'ai_summary': 'This Subaru Forester has an excellent recorded history. The auction grade of 4.5 indicates the vehicle was in near-excellent condition at the time of auction with only very minor imperfections noted. There are no recorded accidents, no theft records, and no open recalls. The mileage appears genuine and consistent with the vehicle age. This vehicle appears to be a reasonable purchase, but we always recommend an independent mechanical inspection before completing the transaction.',
                'processed_data': {
                    'meta': {'source_country': 'JAPAN', 'identifier': 'SG5098765', 'identifier_type': 'CHASSIS', 'report_type': 'FULL'},
                    'vehicle': {'make': 'Subaru', 'model': 'Forester', 'year': 2013, 'engine': '2.0L 4-Cylinder', 'body_type': 'SUV', 'fuel_type': 'Petrol', 'drive_type': 'AWD'},
                    'brands': [],
                    'accidents': [],
                    'theft': [],
                    'recalls': [],
                    'auction_grade': '4.5',
                    'auction_history': [{'auction_house': 'USS Sapporo', 'date': '2020-02-05', 'grade': '4.5', 'odometer_km': 61000}],
                    'odometer_records': [{'date': '2020-02-05', 'reading': 61000, 'unit': 'km'}],
                    'uganda_eligibility': {'eligible': True, 'vehicle_age_years': 12, 'max_allowed_years': 15, 'note': 'Within the 15-year URA import limit'},
                    'risk_score': 92, 'overall_grade': 'A',
                },
            },
        ]

        created_reports = []
        for i, data in enumerate(reports_data):
            user = users[i % len(users)]
            search, _ = VehicleSearch.objects.get_or_create(
                identifier=data['identifier'],
                defaults={
                    'identifier_type': data['identifier_type'],
                    'source_country': data['source_country'],
                    'user': user,
                }
            )
            report, created = VehicleReport.objects.get_or_create(
                search=search,
                report_type=data['report_type'],
                defaults={
                    'user': user,
                    'status': VehicleReport.COMPLETED,
                    'overall_grade': data['overall_grade'],
                    'risk_score': data['risk_score'],
                    'ai_summary': data['ai_summary'],
                    'processed_data': data['processed_data'],
                    'completed_at': timezone.now() - timedelta(days=random.randint(1, 30)),
                    'is_public': i == 0,
                }
            )
            created_reports.append(report)

        self.stdout.write(f'  Created/found {len(created_reports)} vehicle reports.')
        return created_reports

    def _seed_orders(self, users, reports):
        from apps.payments.models import Order
        payment_methods = [Order.MTN, Order.AIRTEL, Order.CARD_FLW]
        created = 0
        for i, report in enumerate(reports[:5]):
            user = users[i % len(users)]
            amount = 75000 if report.report_type == 'FULL' else 35000
            _, was_created = Order.objects.get_or_create(
                report=report,
                defaults={
                    'user': user,
                    'report_type': report.report_type,
                    'amount_ugx': amount,
                    'amount_usd': round(amount / 3720, 2),
                    'payment_method': random.choice(payment_methods),
                    'payment_status': Order.COMPLETED,
                    'flutterwave_ref': f'FLW-MOCK-{random.randint(100000000, 999999999)}',
                    'customer_email': user.email,
                    'paid_at': timezone.now() - timedelta(days=random.randint(1, 30)),
                }
            )
            if was_created:
                created += 1
        self.stdout.write(f'  Created {created} orders.')

    def _seed_contacts(self):
        from apps.core.models import ContactMessage
        if ContactMessage.objects.count() >= 5:
            self.stdout.write('  Contacts already seeded, skipping.')
            return

        contacts = [
            {
                'name': 'Emmanuel Kyomugisha',
                'email': 'emmanuel.k@gmail.com',
                'phone': '256772100200',
                'subject': ContactMessage.GENERAL,
                'message': 'I am about to buy a Toyota Harrier from a dealer in Ntinda and would like to verify its history before paying. The chassis number is ACU30-1234567. Can you help me check this vehicle?',
                'status': ContactMessage.UNREAD,
            },
            {
                'name': 'Prossy Namuwaya',
                'email': 'prossy.namuwaya@yahoo.com',
                'phone': '256756300400',
                'subject': ContactMessage.PAYMENT_PROBLEM,
                'message': 'I paid for a Full Report via MTN Mobile Money yesterday but my money was deducted and I did not receive any report. My transaction reference is FLW-MOCK-987654321. Please help me resolve this urgently.',
                'status': ContactMessage.READ,
            },
            {
                'name': 'Geoffrey Mwesigwa',
                'email': 'g.mwesigwa@outlook.com',
                'phone': '256700500600',
                'subject': ContactMessage.DEALER_INQUIRY,
                'message': 'I am a car dealer with a showroom in Mbarara. I am interested in the dealer account package for 25 reports. Could you please explain how the application process works and what documentation I need to provide?',
                'status': ContactMessage.REPLIED,
            },
            {
                'name': 'Christine Nakiganda',
                'email': 'c.nakiganda@gmail.com',
                'phone': '256704700800',
                'subject': ContactMessage.REPORT_ISSUE,
                'message': 'The report I received shows the car has a rebuilt title. I am not entirely sure what this means for importing it to Uganda. Should I be worried? The car is a 2015 Toyota Vitz from Japan.',
                'status': ContactMessage.UNREAD,
            },
            {
                'name': 'Johnson Atugonza',
                'email': 'johnson.atugonza@gmail.com',
                'phone': '256789900100',
                'subject': ContactMessage.GENERAL,
                'message': 'I could not find the VIN on the car I want to buy from a dealer in Nateete. The seller says the number is on the dashboard but when I look through the windscreen I cannot read it clearly. The car is a 2014 Toyota Corolla from USA. What should I do?',
                'status': ContactMessage.UNREAD,
            },
        ]

        for data in contacts:
            ContactMessage.objects.create(**data)
        self.stdout.write(f'  Created {len(contacts)} contact messages.')

    def _seed_dealer_applications(self):
        from apps.core.models import DealerApplication
        if DealerApplication.objects.count() >= 3:
            self.stdout.write('  Dealer applications already seeded, skipping.')
            return

        applications = [
            {
                'business_name': 'Entebbe Auto Hub',
                'contact_person': 'Moses Ssali',
                'email': 'moses@entebbeautohub.ug',
                'phone': '256700800900',
                'physical_address': 'Plot 12, Entebbe Road, Entebbe',
                'district': 'Wakiso',
                'monthly_sales_volume': '6-15',
                'how_did_you_hear': 'Referral from Kampala Auto Mart',
                'message': 'We have been importing cars from Japan for 6 years and would like to offer history verification as a value-added service to our customers.',
                'status': DealerApplication.PENDING,
            },
            {
                'business_name': 'Kabale Motor Centre',
                'contact_person': 'Edith Tumuhimbise',
                'email': 'edith@kabalemc.ug',
                'phone': '256700100200',
                'physical_address': 'Main Street, Kabale Town',
                'district': 'Kabale',
                'monthly_sales_volume': '1-5',
                'how_did_you_hear': 'Google Search',
                'status': DealerApplication.APPROVED,
            },
            {
                'business_name': 'Mbale Central Autos',
                'contact_person': 'Isaac Wafula',
                'email': 'isaac@mbalecentralautos.ug',
                'phone': '256700300400',
                'physical_address': 'Republic Street, Mbale',
                'district': 'Mbale',
                'monthly_sales_volume': '6-15',
                'how_did_you_hear': 'Facebook',
                'status': DealerApplication.PENDING,
            },
        ]

        for data in applications:
            DealerApplication.objects.create(**data)
        self.stdout.write(f'  Created {len(applications)} dealer applications.')
