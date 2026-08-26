# Terim sözlüğü

Her terimin yanında repo'da nerede karşına çıkacağı yazılı. Sıra kabaca boru
hattının sırası; alfabetik değil, çünkü terimler birbirini gerektiriyor.

## Problem

**architectural intent** — Bir sembolün *ne için* yazıldığı. Tahmin etmeye
çalıştığımız şey. "Veritabanına yazıyor mu" mekanik bir gerçek ve grafın işi;
"bu bir iş kuralı mı yoksa sadece veri mi şekillendiriyor" bir yargı ve modelin
işi.
→ `contracts/taxonomy.v1.yaml`, `docs/taxonomy.md`

**outDegree / inDegree** — Sembolün kaç farklı şeyi çağırdığı / kaç yerden
çağrıldığı. Aralarındaki asimetri mimariyi belirliyor: outDegree'yi tek dosyaya
bakarak bulabilirsin, inDegree'yi bulamazsın — bütün kod tabanını görmen gerekir.
→ `contracts/feature-spec.v1.json` (`degree` grubu)

**graph-global / file-local** — Bir feature'ın bütün grafiği mi yoksa tek dosyayı
mı gerektirdiği. Graph-global feature kullandığın anda sınıflandırma dosya bazlı
incremental olamıyor: hiç değişmemiş bir sembol, başka bir dosya onu çağırmaya
başladığı için sınıf değiştirebiliyor.
→ `features/spec.py` → `NumericField.is_graph_global`

## Feature engineering

**feature engineering** — Ham veriyi modele verilebilir sayılara çevirme işi.
Belirlenimci: aynı girdi her zaman aynı çıktı. Öğrenme içermiyor, ve bu boru
hattının çoğunu kaplıyor.
→ `features/` paketinin tamamı

**token** — Bir identifier'ın bölünmüş hali. `placeOrder` → `place`, `order`.
→ stage 1, `features/lexical.py`

**namespace** — Feature string'inin başındaki kaynak etiketi: `name:`, `callee:`,
`path:`. Aynı kelimenin nereden geldiğini ayırıyor, ki `name:validate` ile
`callee:validate` farklı sinyaller olarak kalsın.
→ stage 2, `contracts/feature-spec.v1.json` → `lexical.namespaces`

**feature hashing** — Feature string'ini sabit boyutlu bir vektörde bir pozisyona
indirmek. Amaç anlam üretmek değil, sözlük tutmayı gereksiz kılmak. Seçilen
fonksiyon MurmurHash3 x86_32, sabit seed.
→ `features/hashing.py`

**collision (çarpışma)** — İki farklı feature string'inin aynı kovaya düşmesi.
Sabit boyutlu uzayın kaçınılmaz bedeli; bir sembol 4096 kovanın ~20'sini
kullandığı için seyrek kalıyor.
→ `make explain` çıktısında görünür

**binary presence** — Bir feature'ın kaç kez geçtiğini değil, geçip geçmediğini
kaydetmek (`1` ya da `0`). Tekrar sayısı zaten sayısal blokta temsil ediliyor;
aynı bilgiyi iki yerden vermek modele yardım etmiyor.
→ `contracts/feature-spec.v1.json` → `hash.occurrence`

**sparse (seyrek)** — Çoğu elemanı sıfır olan vektör. 4163 pozisyonun ~35'i dolu
olduğu için sadece sıfırdan farklı olanlar saklanıyor.
→ `features/build.py` (`csr_matrix`)

**StandardScaler / ölçekleme** — Sayısal bloğu ortak bir ölçeğe çekmek
(ortalamayı çıkar, yayılıma böl). Olmazsa `inDegree = 47` gibi tek bir değer
diğer dört bin pozisyonu bastırıyor.
→ stage 4

**data leakage (sızıntı)** — Test verisinin eğitime sızması. Buradaki tipik
hâli: ölçekleyiciyi bütün veri üstünde fit etmek. Hata vermiyor, sadece bütün
skorları olduğundan iyi gösteriyor.
→ `pipeline.py` → `_run_fold`

## Model

**logistic regression** — Adında "regression" geçse de sınıflandırma için
kullanılıyor. Öğrendiği şeyin tamamı bir ağırlık matrisi ve bir bias vektörü.
Tek katmanlı bir sinir ağı olarak da okunabilir.
→ stage 5, `model/train.py`

**logit** — Softmax'tan önceki ham skor. Aralığı belirsiz; tek başına anlamı yok,
sadece birbirleriyle karşılaştırılabilir.
→ `model/artifact.py` → `predict_proba`

**softmax** — Skorları toplamı 1 olan olasılıklara çeviren fonksiyon. Üstel alma
iki iş birden yapıyor: negatifleri pozitife çeviriyor ve farkı keskinleştiriyor.
→ `model/artifact.py`

**cross-entropy** — Kayıp fonksiyonu. Doğru sınıfa düşük olasılık verilmesini
cezalandırıyor, ve emin olup yanılmayı özellikle ağır cezalandırıyor. Model bu
yüzden temkinli olmayı öğreniyor.
→ sklearn'ün içinde; doğrudan yazmıyorsun

**regularization / `C`** — Ağırlıkların büyümesini cezalandırarak ezberlemeyi
engelleyen ayar. ~200 örneğe karşı 4163 feature varken kritik: kısıtsız bir model
her örneğe özel bir feature bulup eğitimde %100 alır, yeni bir sembolde çöker.
Küçük `C` = daha sıkı kısıt = daha basit model.
→ `config.py` → `TrainingConfig.regularisation`

**class_weight="balanced"** — Nadir sınıftaki hatayı pahalı hale getiriyor.
Olmazsa model "her şeye en kalabalık sınıfı de" stratejisini keşfediyor — ki
accuracy için gerçekten iyi bir strateji, bizim için işe yaramaz.
→ `config.py`

**çıkarım (inference)** — Eğitilmiş modeli yeni bir girdiye uygulamak. Bu sırada
model **hiçbir şey öğrenmiyor**; sadece donmuş `W` ve `b` ile hesap yapıyor.
→ `model/artifact.py` → `predict_proba`

## Ölçme

**accuracy** — Doğru bilinen oran. Tek başına yanıltıcı: sınıflar dengesizken en
kalabalık sınıfı ödüllendiriyor. Raporda geçiyor ama asla yalnız değil.
→ `evaluation/metrics.py`

**macro-F1** — Her sınıfın F1'ini ayrı hesaplayıp **eşit ağırlıkla** ortalamak.
Kalabalık sınıfı bilip diğer dokuzunu bilmemek yüksek skor getirmiyor.
Raporlanacak asıl sayı bu.
→ `evaluation/metrics.py`

**precision / recall** — Precision: "bu sınıf dediklerimin kaçı doğruydu".
Recall: "bu sınıf olanların kaçını yakaladım". F1 ikisinin dengesi.
→ `evaluation/results.py` → `ClassMetrics`

**support** — Bir sınıfın test verisindeki gerçek örnek sayısı.

**low-N** — Örnek sayısı fold sayısından az olduğu için sonucu gürültü sayılması
gereken sınıf. İşaretlenmezse tabloda diğerleriyle aynı ağırlıkta görünüyor ve
yanlış karar verdiriyor.
→ `evaluation/folds.py` → `low_n_classes`

**stratified k-fold** — Veriyi k parçaya bölerken her parçada sınıf oranlarını
koruyan çapraz doğrulama. Her örnek tam bir kez test ediliyor, hepsi eğitimde de
kullanılıyor — az etiketin varken veriyi israf etmemek için.
→ `evaluation/folds.py`

**coverage** — Modelin eşiği geçip cevap verebildiği sembollerin oranı. "%92
doğruluk" cümlesi bu olmadan hiçbir şey ifade etmiyor; sembollerin %5'ine cevap
veriyor olabilirsin.
→ `evaluation/metrics.py`

**precision@covered** — Cevap verdiklerinin içindeki isabet oranı. Coverage ile
takas ediliyor: eşiği yükselt, precision artar coverage düşer.

**abstention** — Modelin "bilmiyorum" deme oranı. Coverage'ın diğer yüzü.

**calibration (kalibrasyon)** — Modelin verdiği olasılığın gerçek isabet oranıyla
örtüşmesi. Softmax'ın verdiği `0.94` gerçek bir olasılık gibi *görünüyor* ama
olduğu garanti değil. Kontrol basit ve zorunlu: accept kovasındaki isabet oranı
gerçekten tentative'inkinden yüksek mi?
→ `evaluation/results.py` → `Calibration.separates`

**confusion matrix** — Hangi sınıfın hangisiyle karıştırıldığını gösteren tablo.
Taksonomi zaten nerede karışacağını öngörüyor: validator ↔ policy, orchestrator ↔
domain_logic.
→ `evaluation/confusion.py`

**ablation** — Bir bileşeni çıkarıp sonucun ne kadar düştüğüne bakarak katkısını
ölçmek. Buradaki dört varyant: A (sadece isimler), B-local, B-global, C (hepsi).
A tek başına C'ye yakın skor veriyorsa model kelime eşleştirmesi yapıyor demektir
— ve kelime eşleştirmesi farklı isimlendirme geleneği olan bir repo'da çöker.
→ `experiments/ablation.py`

## Sözleşme

**featureVersion / taxonomyVersion** — Vektörün düzeni ve etiket listesi ayrı
sürüm numaraları taşıyor, çünkü bağımsız değişiyorlar: taksonomi değişince
vektör aynı kalıyor, yeni bir sayaç eklenince sınıflar aynı kalıyor.
→ `contracts/model-artifact.md`

**golden fixture** — İki dilin de okuyup aynı sonucu üretmesi gereken referans
dosya. Parity'nin sessizce bozulmasını yakalayan tek mekanizma.
→ `contracts/fixtures/`

**parity** — Python (eğitim) ve TypeScript (çıkarım) taraflarının birebir aynı
sayıları üretmesi. Bozulduğunda **hata vermiyor**, sadece sonuç kötüleşiyor.
→ `features/hashing.py`, `tests/test_hashing.py`

**artifact** — Eğitilmiş modelin dosya hâli: ağırlıklar, bias, sınıf isimleri,
ölçekleyici parametreleri ve sürümler. Üretime giden şeyin tamamı.
→ `contracts/model-artifact.md`, `model/artifact.py`
