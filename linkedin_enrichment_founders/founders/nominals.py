# This file contains lists of degree titles awarded to graduates at the Doctor, Master and Bachelor levels.
# The lists contain mostly titles awarded in Germany and Anglophone countries.
# The titles are used to identify what level of study a person has achieved.
#   E.g. a person may have written their description as "Master of Science (M.Sc.) Electrical Engineering"
#        These lists are used to identify the substring "MSc" or "Master of Science" and give this person the education level of "Masters"
# The matching is relaxed so punctuation like periods, hyphens, and spaces do not need to be  

DOCTOR_NOMINALS = ["Dr. h.c.",
                    "Dr.-Ing.",
                    "Dr. iur.",
                    "Dr. iur. utr.",
                    "Dr. habil.",
                    "Dr. oec. pub.",
                    "Dr. theol.",
                    "Dr. paed.",
                    "Dr. phil.",
                    "Dr. rer. medic.",
                    "Dr. rer. physiol.",
                    "Dr. rer. nat.",
                    "Dr. rer. biol",
                    "Dr. rer. soc.",
                    "Dr. rer. pol.",
                    "Dr. med.",
                    "Dr. phil. nat",
                    "Docteur en droit",
                    "Doctor of Law",
                    "PhD",
                    "Dr.-Prof",
                    "DPhil",
                    "EngD", 
                    "DLitt", 
                    "DTech", 
                    "DSc",
                    "DPhys",
                    "Doktor",
                    "DProf", "Doctorate", "Doctor", "Dr", "MD", "Doktor (PhD)", "Approbation"
                    "D Prof"]

MBA_NOMINALS = ["Master of Business Administration",
            "MBA",
            "M.B.A.",
            "Executive Masters",
            "Master's in Business Administration",
            "Masters in Business Administration",
            "M.B.A",
            "Master Business Administration",
            "M B A",
            "M.B.A in Business",
            "MBA in Business",
            "MBA Program",
            "M.B.A Program",
            "MBA (Business Administration)",
            "M.B.A (Business Administration)",
            "MBA Degree",
            "M.B.A Degree",
            "Masters of Business Administration",
            "M.B.A. Degree",
            "Masters in Business Admin",
            "Masters in Business Admin.",
            "MBA Exec",
            "Executive MBA",
            "Executive M.B.A.",
            "MBA Executive Program",
            "MBA in Management",
            "M.B.A in Management",
            "MBA/PGDM",
            "PGDM (MBA Equivalent)",
            "MBA (Management)",
            "M.B.A (Management)",
            "MBA (Exec)",
            "M.B.A (Exec)",
            "M.B.A (Executive)",
            "Masters in Bus Admin",
            "Masters in Bus Admin.",
            "Master in Business Admin",
            "Master in Business Admin.",
            "M.B.A in Admin",
            "MBA in Admin",
            "Masters in Business Mgmt",
            "Master of Business Admin",
            "Masters of Business Admin",
            "Masters of Business Admin.",
            "Master in Business Mgmt",
            "MBA in Bus Mgmt",
            "M.B.A in Bus Mgmt",
            "MBA in Business Mgmt",
            "M.B.A in Business Mgmt",
            "MBA - Business Admin",
            "M.B.A - Business Admin",
            "Master Bus Admin",
            "Master Bus Admin.",
            "Masters Bus Admin",
            "Masters Bus Admin."
        ]

MASTER_NOMINALS = ["Master of Arts", "Master of Science", "Master of Research", 
                    "Master of Education", "Master of Commercial Law",
                    "Master of Finance", "Master of Financial Management",
                    "Master of Computer Science", "Master of Mathematics", 
                    "Master of Marketing"
                    "Master of International Business", "Master of Literature", 
                    "Master of Engineering",
                    "Master of Laws", 
                    "Master of Social Work", 
                    "Master of Public Health", 
                    "Master of Industrial Engineering and Management",
                    "MSc", "MAI", "MA", "MSCS", "ME",  "MEng", "MS",
                    "MTech", "MEd", "MFA", "MBA", "MSw",
                    "MDes", "MArch", "MMus", "MDS", 
                    "MPharm", "MVSc", "MTh", "MDS", 
                    "MChD", "MChir", "MMedSci", 
                    "MMed", "MBBS", "MHBMB", "MMin", 
                    "MVetMed", "MBiomedSci", "MBioinf", 
                    "MBiotech", "MScVetBiol", "MEngTech",
                     "MScBioinf", "MAcc", "MScAcc", 
                     "LL.M", "EMBA", 'Master in Supply Chain Management',
                    "MAccSci", "MScAccSci", "Executive Master", "Master of Business Engineering",
                    "Master's Degree", "Master's", "Magistra artium", "Magister", "Magistra",
                     "Master", "Laurea", "Staatsexamen", "maestría", "máster"]


BACHELOR_NOMINALS = ['Bachelor of Science', 
                    "Bachelor of Arts", 
                    "Bachelor of Engineering", 
                    "Bachelor of Business Administration",
                    "Bachelor's Degree",
                    "LLB", "BS", "BFA", "BA", "BEng", "BE",  
                    "BSc", "BEng", "BTech", "BEd", "BBA", "BDes", 
                    "BArch", "BMus", "BDS", "BPharm", "BVSc", "BTh", 
                    "BDS", "BChD", "BChir", "BMedSci", "BMed", "BMBS", 
                    "BHBMB", "BMin", "BVetMed", "BBiomedSci", "BBioinf", 
                    "BBiotech", "BScVetBiol", "BEngTech", "BScBioinf", "BAcc", 
                    "BScAcc", "BAccSci", "BScAccSci", "BE(Hons)", "BSc(Hons)", 
                    "Bachelor", "Licence", "Bachiller"]

APPRENTICESHIP_NOMINALS = ["Betriebswirt (VWA)",
                            "Betriebswirt",
                            "Diplom Kaufmann","Diplom Kauffrau"
                            "IHK",
                            "Dipl Bankbetriebswirt",
                            "Betriebswirtschaftslehre", 'Ausbildung', 'Gewerbliche Schule']

PRE_TERTIARY_NOMINALS = ["High School", "Abitur", "Secondary School", "Senior Secondary", "A Levels", "Fachhochschulreife", "BTEC"]


DIPLOM_NOMINALS = [ "Dipl. oec.", "DiplPhys",
                    "Dipl Ing", 
                    "Dipl. Ing", 
                    "Dipl. Wirtschaftsing", 
                    "Diplom-Ingenieur",
                    "Diplom Ingenieur", 
                    "Dipl. Wirt.-Ing.", 
                    "Diplom-Betriebswirt",
                    "Dipl Betriebswirtin",
                    "Diplom Betriebswirt",
                    "Diplom-Betriebswirt",
                    "Dipl Ing Arch",
                    "Dipl (BA)",
                    "Dipl.-Inform.", 
                    "Diplomphysiker", 
                    "Dipl. Volksw.", 
                    "Dipl.-Wirtschafts-Ing.", 
                    "Dipl. Informatiker",
                    "Dipl.-Ing. oec.", 
                    "Diplom", "German Diploma",
                    "Diplome", 
                    "Dipl.", 
                    "Dipl",
                    "Dipl Wirtschaftsing (FH)", "Diplom (FH)",
                    "Dipl Ing (FH)",
                    "Dipl.Ing (FH)",
                    "Dipl Wirt Ing (FH)",
                    "Dipl Wirt.-Ing (FH)",
                    "Dipl Kfm",
                    "Dipl Inf (FH), Wirtschaftsinformatik",
                    "Diplom Ingenieur (FH)",
                    "Dipl.-Ing (FH)", "(FH)"]


OTHER_DEGREE_NOMINALS = ["Staatl. gepr.", "Staatlich geprüfter", "Staatl. geprüfter", "Supplementary Study (Weiterbildung)"]

EXCEPTIONS_TO_NOMINALS = ["Executive Master Class"]

DEGREE_FIELD_IRRELEVANT_WORDS = ["Studies", "Insititute for", "Note", "berufsbegleitende", "FH", "Institut", "Institut fur" "Department", "Abschlussnote", "GPA", "Abitur", "Schwerpunkt", "Consultant", "Major", "Grande Ecole", "Curriculum", "School of", "Faculty", "State Exam", "Class", "Promotion", "Candidate"]

EXCEPTIONS_TO_JOB_TITLES = ['Assistenz', "Assistentin", "Assistent"]


FOUNDER_INDICATOR_WORDS = ["founder",  "grunder", "cofounder", "mitinhaber", "mitbegründer",
                                "co-founder", "gründer", "gründerin", "ceo", "chief executive officer", "chief technology officer", "chief operating officer"
                                "co-fondateur", "fondateur", "cofondateur", "gründung",
                                "geschäftsführung", "mitgründer", "unternehmensinhaber", 
                                "geschäftsführender", "gesellschafter", "mitgründerin", "company owner", "geschäftsführer", "mitglied der geschäftsleitung",
                                "geschäftsführerin", "geschaftsinhaber", "managing director", "owner",
                                "inhaber", "inhaberin", "gesellschafter", "gesellschafterin", "business owner", "geschäftsführender"]
