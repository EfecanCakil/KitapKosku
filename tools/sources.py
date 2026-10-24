"""Kütüphaneye girecek telifsiz eserlerin listesi.

GUTENBERG: (Gutenberg no, türler, Türkçe ad, Türkçe tanıtım). Yalnızca ABD'de ve Türkiye'de telif süresi dolmuş, özgün dilindeki
(İngilizce) metinler. Başka dillerden İngilizceye eski çeviriler de (Dostoyevski, Tolstoy, Verne…) çevirmen telifi düştüğü için uygun.
TR_*: Türkçe Vikikaynak sayfaları.
Türler: korku, polisiye, macera, bilimkurgu, klasik, turk, oyku, masal
"""

GUTENBERG = [
    # ---------- Korku ----------
    (345, ["korku", "klasik"], "Drakula", "Transilvanya'daki şatosundan Londra'ya göç eden kontun ve onu durdurmaya çalışan bir avuç insanın mektuplar ve günlüklerle anlatılan hikâyesi."),
    (84, ["korku", "bilimkurgu", "klasik"], "Frankenstein", "Ölüye can vermeyi başaran genç bilim insanı Victor Frankenstein ve yarattığı yalnız varlığın trajedisi."),
    (43, ["korku", "klasik"], "Dr. Jekyll ve Bay Hyde", "Saygın bir doktorun içindeki karanlık benliği bir iksirle serbest bırakmasının ürpertici öyküsü."),
    (2147, ["korku", "polisiye", "oyku"], "Poe'nun Eserleri I", "Morgue Sokağı Cinayetleri, Çalınan Mektup ve daha fazlası: modern polisiyenin ve korkunun babasından."),
    (2148, ["korku", "oyku"], "Poe'nun Eserleri II", "Usher Evi'nin Çöküşü, Kuyu ve Sarkaç gibi Poe'nun en karanlık hikâyeleri."),
    (2149, ["korku", "oyku"], "Poe'nun Eserleri III", "Poe'nun gerilim ve gizem dolu öykülerinden üçüncü derleme."),
    (209, ["korku", "klasik"], "Yürek Burgusu", "Kır evinde iki çocuğa bakan mürebbiyenin gördüğü hayaletler gerçek mi, yoksa onun zihninde mi?"),
    (174, ["korku", "klasik"], "Dorian Gray'in Portresi", "Yaşlanmayan genç bir adam ve onun yerine çürüyen gizli portresi."),
    (10007, ["korku"], "Carmilla", "Drakula'dan önce yazılmış, ıssız bir şatoya konuk olan gizemli genç kadının vampir hikâyesi."),
    (41, ["korku", "oyku"], "Uykulu Oyuk Efsanesi", "Başsız Süvari efsanesiyle ünlü küçük bir kasabada korkak bir öğretmenin başına gelenler."),
    (175, ["korku", "macera"], "Operadaki Hayalet", "Paris Operası'nın mahzenlerinde yaşayan maskeli dahinin saplantılı aşkı."),
    (8492, ["korku", "oyku"], "Sarı Kral", "Okuyanı deliliğe sürükleyen yasaklı bir oyun etrafında dönen tuhaf hikâyeler."),
    (389, ["korku"], "Büyük Tanrı Pan", "Bir beyin ameliyatıyla 'perdenin ardını' gören kızın yol açtığı kâbuslar zinciri."),
    (68283, ["korku", "oyku"], "Cthulhu'nun Çağrısı", "Lovecraft'ın en ünlü öyküsü: denizin dibinde uyuyan kadim varlık ve onu bekleyen tarikat."),
    (50133, ["korku", "oyku"], "Dunwich Dehşeti", "Issız bir New England köyünde doğan tuhaf çocuk ve tepelerdeki görünmez dehşet."),
    (70652, ["korku", "bilimkurgu"], "Delilik Dağlarında", "Antarktika'ya giden bir bilim heyetinin buzların altında bulduğu kadim şehir."),
    (1952, ["korku", "oyku", "klasik"], "Sarı Duvar Kağıdı", "Odasına kapatılan genç bir kadının duvar kağıdındaki desenlere takılıp kalışı."),
    (696, ["korku", "klasik"], "Otranto Şatosu", "Gotik romanın ilk örneği: lanetli bir şato, dev bir miğfer ve bir hanedanın sırları."),
    (8486, ["korku", "oyku"], "Bir Antikacının Hayalet Hikâyeleri", "M. R. James'in eski kiliseler, el yazmaları ve lanetli eşyalarla dolu klasik hayalet öyküleri."),
    (1188, ["korku"], "Beyaz Solucanın İni", "Bram Stoker'ın son romanı: İngiliz kırsalında yaşayan kadim bir yaratık."),
    (5230, ["bilimkurgu", "korku"], "Görünmez Adam", "Kendini görünmez yapan bir bilim insanının küçük bir kasabada yarattığı kaos."),
    (159, ["bilimkurgu", "korku"], "Dr. Moreau'nun Adası", "Issız bir adada hayvanları insana dönüştürmeye çalışan çılgın bir doktor."),

    # ---------- Polisiye ----------
    (244, ["polisiye"], "Kızıl Dosya", "Sherlock Holmes ile Dr. Watson'ın tanıştığı ilk macera."),
    (2097, ["polisiye"], "Dörtlerin Yemini", "Bir hazine, bir yemin ve tek bacaklı bir adam: Holmes'un ikinci romanı."),
    (1661, ["polisiye", "oyku"], "Sherlock Holmes'un Maceraları", "Bohemya'da Skandal, Kızıl Saçlılar Derneği ve diğer on klasik vaka."),
    (834, ["polisiye", "oyku"], "Sherlock Holmes'un Anıları", "Gümüş Yele, Son Problem ve Holmes'un Moriarty ile karşılaşması."),
    (108, ["polisiye", "oyku"], "Sherlock Holmes'un Dönüşü", "Holmes geri dönüyor: Boş Ev, Dans Eden Adamlar ve daha fazlası."),
    (2852, ["polisiye", "korku"], "Baskerville'lerin Köpeği", "Bataklıkta dolaşan şeytani köpek efsanesi ve Holmes'un en ünlü vakası."),
    (3289, ["polisiye"], "Korku Vadisi", "Bir malikânede işlenen cinayet ve Amerika'daki gizli bir örgütün izi."),
    (2350, ["polisiye", "oyku"], "Son Selam", "Holmes'un savaş yıllarına uzanan son vakaları."),
    (69700, ["polisiye", "oyku"], "Sherlock Holmes'un Vaka Defteri", "Doyle'un Holmes için yazdığı son on iki öykü."),
    (863, ["polisiye"], "Styles'daki Esrarengiz Olay", "Agatha Christie'nin ilk romanı ve Hercule Poirot'nun ilk vakası."),
    (1155, ["polisiye", "macera"], "Gizli Düşman", "Tommy ve Tuppence'ın kayıp bir belgenin peşine düştüğü casusluk macerası."),
    (58866, ["polisiye"], "Golf Sahasında Cinayet", "Poirot, Fransa'da yardım isteyen bir milyonerin cesedini buluyor."),
    (155, ["polisiye", "klasik"], "Aytaşı", "Lanetli bir Hint elmasının çalınması: ilk büyük İngiliz polisiye romanı."),
    (583, ["polisiye", "klasik"], "Beyazlı Kadın", "Gece yarısı yolda karşılaşılan beyazlar içindeki kadın ve bir miras komplosu."),
    (204, ["polisiye", "oyku"], "Peder Brown'ın Saflığı", "Sıradan görünen bir rahibin insan ruhunu okuyarak çözdüğü suçlar."),
    (223, ["polisiye", "oyku"], "Peder Brown'ın Bilgeliği", "Chesterton'ın sevimli dedektif rahibinden yeni vakalar."),
    (6133, ["polisiye", "macera"], "Arsène Lupin'in Maceraları", "Kibar hırsız Arsène Lupin, polisle ve Herlock Sholmes'la kedi fare oyununda."),
    (558, ["polisiye", "macera"], "Otuz Dokuz Basamak", "Bir cinayetle suçlanan adamın İskoçya kırlarında casuslardan kaçışı."),
    (4047, ["polisiye"], "Leavenworth Davası", "New York'ta öldürülen zengin bir tüccar ve şüpheli iki yeğen."),
    (1872, ["polisiye"], "Kırmızı Ev Cinayeti", "A. A. Milne'den bir kır evinde kilitli oda gizemi."),
    (434, ["polisiye"], "Döner Merdiven", "Kiralık bir yazlıkta gece yarısı duyulan sesler ve merdivende bir ceset."),

    # ---------- Aksiyon & Macera ----------
    (120, ["macera"], "Define Adası", "Genç Jim Hawkins, korsan Long John Silver ve gömülü hazine haritası."),
    (521, ["macera", "klasik"], "Robinson Crusoe", "Issız bir adaya düşen denizcinin yirmi sekiz yıllık hayatta kalma mücadelesi."),
    (1257, ["macera", "klasik"], "Üç Silahşörler", "D'Artagnan, Athos, Porthos ve Aramis: Biri hepimiz, hepimiz biri için!"),
    (1259, ["macera"], "Yirmi Yıl Sonra", "Üç Silahşörler'in devamı: eski dostlar iç savaşta yeniden bir arada."),
    (1184, ["macera", "klasik"], "Monte Kristo Kontu", "Haksızca zindana atılan Edmond Dantès'in kaçışı, servet bulması ve intikamı."),
    (103, ["macera"], "80 Günde Devr-i Âlem", "Phileas Fogg'un bir iddia uğruna dünyayı seksen günde dolaşma yarışı."),
    (164, ["macera", "bilimkurgu"], "Denizler Altında Yirmi Bin Fersah", "Kaptan Nemo ve efsanevi denizaltı Nautilus ile okyanusların derinliklerine yolculuk."),
    (18857, ["macera", "bilimkurgu"], "Dünyanın Merkezine Yolculuk", "Bir İzlanda yanardağından dünyanın içine inen profesör ve yeğeni."),
    (1268, ["macera"], "Esrarlı Ada", "Balonla kaçan beş adamın bilinmeyen bir adada sıfırdan hayat kurması."),
    (3526, ["macera"], "Balonla Beş Hafta", "Afrika'yı balonla boydan boya geçmeye çalışan üç gezgin."),
    (1842, ["macera"], "Mihail Strogof", "Çar'ın ulağının Sibirya'nın vahşi bozkırlarında hayati bir mesajı taşıması."),
    (421, ["macera"], "Kaçırılan Çocuk", "Amcası tarafından kaçırılıp gemiye satılan David Balfour'un İskoçya maceraları."),
    (2166, ["macera"], "Kral Süleyman'ın Hazineleri", "Afrika'nın bilinmeyen topraklarında efsanevi elmas madenlerinin peşinde."),
    (215, ["macera", "klasik"], "Vahşetin Çağrısı", "Evcil köpek Buck'ın Alaska'nın karlı topraklarında vahşi doğaya dönüşü."),
    (910, ["macera"], "Beyaz Diş", "Yarı kurt yarı köpek Beyaz Diş'in vahşi doğadan insan dünyasına uzanan yolculuğu."),
    (95, ["macera"], "Zenda Mahkûmu", "Taç giyme töreni öncesi kaçırılan krala tıpatıp benzeyen bir İngiliz'in tehlikeli oyunu."),
    (60, ["macera"], "Kızıl Menekşe", "Fransız Devrimi'nde giyotinden aristokratları kurtaran gizemli kahraman."),
    (78, ["macera"], "Maymunların Tarzanı", "Afrika ormanlarında maymunlar tarafından büyütülen Lord Greystoke'un oğlu."),
    (62, ["macera", "bilimkurgu"], "Mars Prensesi", "Mars'a ışınlanan bir Amerikan askerinin dev yaratıklar ve prensesler arasındaki serüveni."),
    (139, ["macera", "bilimkurgu"], "Kayıp Dünya", "Güney Amerika'da dinozorların hâlâ yaşadığı bir yayla keşfediliyor."),
    (82, ["macera", "klasik"], "Ivanhoe", "Haçlı Seferleri sonrası İngiltere'de şövalyeler, turnuvalar ve Robin Hood."),
    (940, ["macera", "klasik"], "Son Mohikan", "Amerika'nın vahşi ormanlarında İngiliz-Fransız savaşı sırasında bir kaçış."),
    (1965, ["macera"], "Kaptan Blood", "Haksızca köle yapılan bir doktorun Karayipler'in en ünlü korsanına dönüşmesi."),
    (1074, ["macera"], "Deniz Kurdu", "Acımasız kaptan Wolf Larsen'in gemisine düşen bir edebiyatçının hayatta kalma mücadelesi."),
    (2701, ["macera", "klasik"], "Moby Dick", "Kaptan Ahab'ın beyaz balinaya duyduğu saplantılı intikam."),
    (829, ["macera", "klasik"], "Gulliver'in Gezileri", "Cüceler, devler, uçan ada ve konuşan atlar: Swift'in hiciv dolu yolculukları."),
    (3836, ["macera"], "İsviçreli Robinson Ailesi", "Gemi kazasından kurtulup ıssız bir adada yeni bir hayat kuran aile."),
    (236, ["macera", "masal"], "Orman Çocuğu", "Kurtlar tarafından büyütülen Mowgli ve Hindistan ormanlarının hikâyeleri."),
    (16, ["macera", "masal"], "Peter Pan", "Hiç büyümeyen çocuk, Kaptan Kanca ve Varolmayan Ülke."),
    (76, ["macera", "klasik"], "Huckleberry Finn'in Maceraları", "Huck ve kaçak köle Jim'in Mississippi Nehri'nde salla yolculuğu."),
    (74, ["macera", "klasik"], "Tom Sawyer'ın Maceraları", "Mississippi kıyısındaki bir kasabada yaramaz Tom'un hazine ve cinayet dolu yazı."),
    (10148, ["macera", "masal"], "Robin Hood'un Neşeli Maceraları", "Sherwood Ormanı'nın efsanevi okçusu ve neşeli adamları."),
    (2610, ["klasik", "macera"], "Notre-Dame'ın Kamburu", "Kambur Quasimodo, çingene kızı Esmeralda ve Ortaçağ Paris'i."),

    # ---------- Bilim Kurgu ----------
    (35, ["bilimkurgu"], "Zaman Makinesi", "Zamanda yolculuk yapan mucidin 802.701 yılında karşılaştığı insanlık."),
    (36, ["bilimkurgu"], "Dünyalar Savaşı", "Marslıların İngiltere'yi istila edişi."),
    (1013, ["bilimkurgu"], "Ay'daki İlk İnsanlar", "Yerçekimini engelleyen bir maddeyle Ay'a giden iki adam."),
    (83, ["bilimkurgu", "macera"], "Ay'a Yolculuk", "Dev bir topla Ay'a mermi göndermeye karar veren Amerikan top kulübü."),
    (32, ["bilimkurgu"], "Kadınlar Ülkesi", "Yalnızca kadınlardan oluşan ütopik bir ülkeye giden üç kâşif."),

    # ---------- Dünya Klasikleri ----------
    (1342, ["klasik"], "Gurur ve Önyargı", "Elizabeth Bennet ve Bay Darcy: önyargıların aşka dönüştüğü ölümsüz roman."),
    (1260, ["klasik"], "Jane Eyre", "Yetim bir mürebbiyenin bağımsızlık ve aşk arayışı, Thornfield Konağı'nın sırrı."),
    (768, ["klasik"], "Uğultulu Tepeler", "Heathcliff ile Catherine'in yıkıcı, tutkulu aşkı."),
    (1400, ["klasik"], "Büyük Umutlar", "Yetim Pip'in gizemli bir hayırseverin yardımıyla beyefendiliğe uzanan yolu."),
    (98, ["klasik"], "İki Şehrin Hikâyesi", "Fransız Devrimi sırasında Londra ve Paris arasında aşk ve fedakârlık."),
    (730, ["klasik"], "Oliver Twist", "Londra sokaklarında hırsız çetesinin eline düşen yetim çocuk."),
    (46, ["klasik", "masal"], "Bir Noel Şarkısı", "Cimri Scrooge'u Noel gecesi ziyaret eden üç hayalet."),
    (2554, ["klasik", "polisiye"], "Suç ve Ceza", "Raskolnikov'un işlediği cinayet ve vicdanıyla hesaplaşması."),
    (28054, ["klasik"], "Karamazov Kardeşler", "Bir baba, dört oğul ve bir cinayet: Dostoyevski'nin başyapıtı."),
    (2638, ["klasik"], "Budala", "Saf ve iyi kalpli Prens Mışkin'in Petersburg sosyetesindeki trajedisi."),
    (600, ["klasik"], "Yeraltından Notlar", "Toplumdan kopmuş bir adamın acı ve ironik itirafları."),
    (1399, ["klasik"], "Anna Karenina", "Yasak bir aşkın Rus aristokrasisindeki yıkıcı sonuçları."),
    (2600, ["klasik"], "Savaş ve Barış", "Napolyon savaşları sırasında beş Rus ailesinin hayatı."),
    (135, ["klasik"], "Sefiller", "Eski kürek mahkûmu Jean Valjean'ın kurtuluş arayışı ve Javert'in takibi."),
    (996, ["klasik", "macera"], "Don Kişot", "Şövalye romanlarıyla aklını yitiren soylunun ve uşağı Sancho'nun maceraları."),
    (2413, ["klasik"], "Madam Bovary", "Taşra hayatından sıkılan Emma Bovary'nin hayalleri ve düşüşü."),
    (64317, ["klasik"], "Muhteşem Gatsby", "Caz Çağı'nda gizemli milyoner Gatsby'nin kayıp aşkına uzanan rüyası."),
    (11, ["klasik", "masal"], "Alice Harikalar Diyarında", "Bir tavşan deliğinden düşen Alice'in akıl almaz dünyası."),
    (37106, ["klasik"], "Küçük Kadınlar", "March kardeşlerin savaş yıllarında büyüme hikâyesi."),
    (33, ["klasik"], "Kızıl Damga", "Püriten Boston'da göğsünde kırmızı 'A' harfi taşıyan kadın."),
    (5200, ["klasik"], "Dönüşüm", "Bir sabah dev bir böceğe dönüşmüş olarak uyanan Gregor Samsa."),
    (7849, ["klasik", "polisiye"], "Dava", "Neyle suçlandığını hiç öğrenemeyen Josef K.'nın bitmeyen davası."),
    (219, ["klasik", "macera"], "Karanlığın Yüreği", "Kongo Nehri'nde gizemli Kurtz'u arayan Marlow'un yolculuğu."),
    (2500, ["klasik"], "Siddhartha", "Hindistan'da aydınlanma arayan genç bir Brahman'ın yolculuğu."),
    (19942, ["klasik"], "Candide", "Voltaire'in iyimserliği tiye aldığı, felaketten felakete koşan saf gencin hikâyesi."),
    (158, ["klasik"], "Emma", "Çöpçatanlığa meraklı Emma Woodhouse'un karıştırdığı aşk hayatları."),
    (161, ["klasik"], "Akıl ve Tutku", "Dashwood kardeşlerin aşkla ve toplumla sınavı."),
    (1727, ["klasik", "macera", "masal"], "Odysseia", "Truva Savaşı'ndan dönen Odysseus'un on yıllık eve dönüş yolculuğu."),
    (203, ["klasik"], "Tom Amca'nın Kulübesi", "Kölelik karşıtı hareketi ateşleyen roman."),
    (145, ["klasik"], "Middlemarch", "Bir İngiliz taşra kasabasında hayaller, evlilikler ve hayal kırıklıkları."),

    # ---------- Masal ----------
    (2591, ["masal"], "Grimm Masalları", "Kırmızı Başlıklı Kız, Hansel ile Gretel, Pamuk Prenses ve daha nicesi."),
    (1597, ["masal"], "Andersen Masalları", "Çirkin Ördek Yavrusu, Küçük Deniz Kızı, Kibritçi Kız ve diğerleri."),
    (128, ["masal", "macera"], "Binbir Gece Masalları", "Şehrazat'ın anlattığı Alaaddin, Ali Baba ve Sinbad'ın hikâyeleri."),
]

# Gutenberg künyesindeki yazar adı okunaksız olanlar
AUTHORS = {
    1184: "Alexandre Dumas", 1257: "Alexandre Dumas", 1259: "Alexandre Dumas", 60: "Baroness Orczy",
    2591: "Grimm Kardeşler", 2600: "Lev Tolstoy", 1399: "Lev Tolstoy", 996: "Miguel de Cervantes",
    84: "Mary Shelley", 10007: "Sheridan Le Fanu", 128: "Andrew Lang (derleyen)",
}
TITLES = {2350: "His Last Bow", 83: "From the Earth to the Moon", 16: "Peter Pan", 829: "Gulliver's Travels",
          1842: "Michael Strogoff", 46: "A Christmas Carol"}

# Ömer Seyfettin'in kahramanlık ve tarih konulu hikâyeleri ayrı bir kitapta toplanır; kalanlar "Seçme Hikâyeler"e girer.
OMER_SEYFETTIN_TARIHI = ["Forsa", "Başını Vermeyen Şehit", "Pembe İncili Kaftan", "Kızıl Elma Neresi?", "Ferman", "Diyet",
                         "Topuz", "Vire", "Teselli", "Kerâmet", "Tuğra", "Külah", "Gizli Mâbed", "And", "Kurumuş Ağaçlar",
                         "Yıkık Han", "Nasıl Kurtarmış?", "Hürriyet Bayrakları"]

TR_NOVELS = [
    ("Kürk Mantolu Madonna", "Sabahattin Ali", 1943, ["turk", "klasik"],
     "Ankara'da sıradan bir memur olan Raif Efendi'nin defterinden, 1920'lerin Berlin'inde ressam Maria Puder'e duyduğu sessiz ve derin aşk."),
]

TR_MASAL_CATEGORY = "Kategori:Türk halk edebiyatında masallar"
