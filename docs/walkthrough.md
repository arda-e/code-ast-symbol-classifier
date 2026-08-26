# Bir sembol nasıl sayıya, sayı nasıl tahmine dönüşüyor

Bu doküman tek bir fonksiyonu baştan sona takip ediyor. Buradaki bütün sayılar
uydurma değil — `contracts/fixtures/vector-golden.json` içinde duruyorlar ve
testler tam olarak bunları doğruluyor.

Aynı şeyi canlı görmek için:

```bash
make explain
```

Boş slot'lar varken bile çalışır; her aşama ya çıktısını basar ya da "henüz
yazılmadı" deyip hangi teste bakman gerektiğini söyler.

---

## 0. Sorumuz ne

Elimizdeki fonksiyon:

```ts
async placeOrder(input: CreateOrderDto) {
  const order = await this.orderFactory.create(input);
  await this.inventory.reserve(order.items);
  await this.payment.charge(order);
  await this.repository.save(order);
  return order;
}
```

Sorduğumuz soru "bu ne yapıyor" değil — **"bu neden yazılmış"**. Ne yaptığını
graf zaten biliyor: veritabanına yazıyor, dört şey çağırıyor, async. Bilmediği
şey, bu fonksiyonun kendi başına hiçbir karar vermediği, değerinin tamamen dört
birimi doğru sırayla dizmekte olduğu. Yani `orchestrator`.

Testi basit: **çağrılarını silersen geriye bir kural kalıyor mu?** Kalmıyorsa
orchestrator.

---

## 1. Modele giden şey ne — ve ne gitmiyor

Sezgi burada genelde yanlış çıkıyor, o yüzden en başta netleştirelim.

Modele fonksiyonun **gövdesi gitmiyor.** Ne `if` blokları, ne değişken adları,
ne yorumlar. Model bunları görüyor:

```
isimden gelenler                    isimden gelmeyenler
─────────────────                   ───────────────────
sembolün adı      placeOrder        outDegree, inDegree
sahibi            OrderService      async, exported, paramCount
dosya yolu        src/orders/...    karşılaştırma / dallanma / await sayaçları
çağırdıklarının   create, reserve   yan etkiler, mutasyonlar
adları            charge, save
parametre tipi    CreateOrderDto
dönüş tipi        Promise<Order>
```

Sağ sütundaki her şey parser'ın çıkardığı sayılabilir gerçekler; sol sütun
isimler. Dikkat: **çağırdığı fonksiyonların isimleri gövdeden geliyor** — parser
içeri bakıp `this.payment.charge(order)` satırını buluyor. Yani bilgi gövdeden
çıkıyor, ama modele bir isim olarak ulaşıyor.

---

## 2. İsimleri kelimelere böl  *(stage 1)*

```
placeOrder              →  place, order
CreateOrderDto          →  create, order, dto
isEligibleForDiscount   →  is, eligible, for, discount
```

**Neden bölüyoruz?** Bölmezsen `placeOrder` tek başına bir kova olur ve
`placeBid`, `cancelOrder`, `orderTotal` ile hiçbir ortak sinyal paylaşmaz. Model
hiçbir şey genelleştiremez — sadece daha önce gördüğü tam isimleri tanır. Bölünce
`order` kelimesi bütün bu isimler arasında ortak bir sinyal haline geliyor.

---

## 3. Her kelimenin nereden geldiğini yaz  *(stage 2)*

`placeOrder` için üretilen 21 string:

```
name:place       name:order
owner:order      owner:service
path:src         path:orders        path:order       path:service
callee:order     callee:factory     callee:create
callee:inventory callee:reserve
callee:payment   callee:charge
callee:repository callee:save
accepts:create   accepts:order      accepts:dto
returns:order
```

**Neden başlarına etiket koyuyoruz?** Çünkü aynı kelime, geldiği yere göre
bambaşka bir şey anlatıyor:

```
name:validate      bu fonksiyonun kendi adında "validate" geçiyor
                   → büyük ihtimalle validator

callee:validate    bu fonksiyon, doğrulama yapan başka bir şeyi çağırıyor
                   → kendisi doğrulamıyor; belki orchestrator
```

Etiket olmasa ikisi de aynı kovaya düşer ve model aradaki farkı **asla**
öğrenemez.

İki küçük karar daha, ikisi de sözleşmede yazılı:

- **Çağrıda alıcıyı da alıyoruz.** `save` her yerde geçiyor, `repository.save`
  geçmiyor. Alıcı çoğu zaman metot adından daha güçlü sinyal.
- **`this` atılıyor.** Neredeyse her metot çağrısında var, hiçbir şey ayırmıyor,
  boşuna kova harcıyor.

---

## 4. String'leri kovalara indir  *(hash)*

Buradaki fikri doğru kurmak önemli. Hash'i **kelimeyi sayıya çevirmek** için
kullanmıyoruz; sınırsız sayıda olabilecek string'i **sabit boyutlu bir uzayda bir
kovaya yerleştirmek** için kullanıyoruz.

Alternatif bir sözlük tutmak olurdu — ama gerçek bir kod tabanında yüz binlerce
identifier var, her yeni repoda yenileri çıkıyor, ve o sözlüğü üretmek, saklamak,
sürümlemek ve **iki dil arasında taşımak** gerekiyor. Hash bunu tamamen ortadan
kaldırıyor.

Gerçek sayılar (`hash-golden.json`'dan):

```
"name:place"        →  murmur3 →  % 4096  →   669
"owner:service"     →  murmur3 →  % 4096  →   677
"path:src"          →  murmur3 →  % 4096  →   200
"path:service"      →  murmur3 →  % 4096  →  3791
"name:order"        →  murmur3 →  % 4096  →  2966
```

Sonuç 4096 uzunluğunda bir vektör; 21 pozisyonu 1, gerisi 0.

> **Bu kısım repo'nun en kırılgan yeri.** Aynı hash'in ileride TypeScript
> tarafında birebir aynı sonucu vermesi gerekiyor. Yanlış olursa **hata vermez** —
> sessizce daha kötü tahmin eder. O yüzden hash fonksiyonu kendi modülünde
> (`features/hashing.py`), config'i sözleşmede, ve `hash-golden.json` iki dilin de
> okuyacağı ortak fixture olarak duruyor.
>
> Parity'yi bozan dört ayrıntı, dördü de sessiz: varyant (x86_32 mi x64_128 mi),
> seed, işaret (`signed=False` şart — negatif sayıda `%` Python ve JavaScript'te
> farklı davranıyor) ve kodlama.

**Çarpışma.** Sınırsız string'i sabit uzaya sığdırdığın için iki farklı
feature'ın aynı kovaya düşmesi kaçınılmaz. Tolere edilebiliyor, çünkü bir sembol
4096 kovanın yalnızca ~20'sini kullanıyor.

---

## 5. Zaten sayı olanları hash'leme  *(stage 3)*

Bazı bilgiler zaten sayı ve **kapalı bir küme** oluşturuyor — kaç tane yan etki
türü varsa o kadar. Kapalı kümeler sabit pozisyon alıyor. `placeOrder` için:

```
[ 0] outDegree                   4        [12] paramCount                1
[ 1] inDegree                    3        [13] statementCount            5
[ 2] distinctCallees             4        [14] lineCount                 7
[ 3] distinctCallers             3        [20] awaitCount                4
[ 4] entrypointDistance          1        [21] returnCount               1
[ 5] isAsync                     1        [48] sideEffect_database_write 1
[ 6] isExported                  1
[11] isMethod                    1        → 67 pozisyonun 14'ü dolu
```

**Neden bunları metne gömmüyoruz?** Diyelim modele `calls: create, reserve,
charge, save` diye metin verdik. Modelin buradan `outDegree = 4` sonucuna varması
için sırayla üç şey yapması gerekir: virgülün ayırıcı olduğunu anlamak, parçaları
saymak, o sayıyı "derece" kavramına bağlamak. Üçü de garanti değil, ve model
bunları öğrenirken tek geri bildirimi sınıf etiketi. `outDegree = 4` deyince
sayma işi zaten yapılmış oluyor.

**Sıra bir sözleşme.** İki pozisyonu takas edersen `comparisonCount`,
`paramCount`'un ağırlığıyla çarpılır. Hata vermez. Sadece skor düşer, ve nedenini
sonradan bulmak neredeyse imkânsız.

---

## 6. İki bloğu birleştir ve ölçekle  *(stage 4)*

```
[0,0,...,1,...,1,...,0]  +  [4, 3, 4, 3, 1, ...]
└──── 4096 kova, 0/1 ───┘    └── 67 sayı, ölçekli ──┘
                  4163 sayı
```

Toplama yok, karıştırma yok — uç uca yapıştırma. Model her pozisyona ayrı bir
ağırlık öğreniyor ve sayının nereden geldiğini umursamıyor.

**Neden ölçekliyoruz?** Hash bloğundaki değerler 0 veya 1. Ama sayısal blokta
`inDegree = 47` gibi bir değer, dört bin sıfır ve birin yanında devasa duruyor ve
eğitim sırasında tek başına diğer hepsini bastırabiliyor. Standartlaştırma
(ortalamayı çıkar, yayılıma böl) hepsini kıyaslanabilir hale getiriyor.

**Ölçekleyici neden `fit` ve `transform` diye ayrı?** Ortalamayı **sadece eğitim
satırlarından** öğrenmesi gerekiyor. Her şeyin üstünde fit edersen, test
satırları kendilerini puanlayan sayıları sessizce etkilemiş olur; her sonuç
modelin gerçekte olduğundan iyi çıkar ve **hiçbir uyarı almazsın.** Bu ayrım o
sızıntıyı engelleyen tek şey.

---

## 7. Vektörden olasılığa  *(stage 5)*

Öğrenilen şeyin tamamı bir ağırlık tablosu ve bir bias vektörü:

```
ağırlık matrisi:   10 sınıf × 4163 feature
bias:              10 sayı
```

Tahmin:

```
skorlar = W × x + b          → 10 ham sayı (logit)
softmax(skorlar)             → toplamı 1 olan 10 olasılık
```

`make explain --symbol isEligible` çıktısı (gerçek bir koşudan):

```
domain_logic     0.799  ████████████████████████
policy           0.085  ███
unknown          0.056  ██
utility          0.018  █

tentative — domain_logic, worth a human glance
```

**Neden tek etiket yetmiyor?** Şu ikisi top-1 alındığında birbirinin aynı
görünüyor:

```
orchestrator 0.94        orchestrator 0.45
domain_logic 0.04        domain_logic 0.40
   model emin               yazı tura
```

İkisi de "orchestrator" diyor. Dağılımın şekli, etiketin kendisinden daha
bilgilendirici.

**Üç kova:**

```
güven ≥ 0.85   →  accept       kabul et
güven ≥ 0.65   →  tentative    şüpheli, insan baksın
altı           →  unknown      tahmini at
```

Yanlış etiket vermektense etiketsiz bırakmak daha ucuz — yanlış bir mimari rol,
grafiğe güvenen her sorguya yayılıyor.

> Bu üç eşik şu an bir **varsayım**, ölçüm değil. `evaluation/metrics.py`'daki
> kalibrasyon kontrolü tam olarak bunu sınıyor: accept kovasındaki isabet oranı
> gerçekten tentative'inkinden yüksek mi? Değilse eşik hiçbir şey ayırmıyor
> demektir.

---

## 8. Bu boru hattının neresi makine öğrenmesi?

Bu soruyu erken sormak önemli, çünkü cevabı çoğu insanın beklediğinden dar.

```
     placeOrder
          ↓
       böl                   ┐
          ↓                  │
     etiketle                ├─  feature engineering
          ↓                  │   (makine öğrenmesi DEĞİL)
       hash'le               │
          ↓                  │
   sayısal bloğu ekle        │
          ↓                  │
   4163 boyutlu vektör       ┘
          ↓
   ┌──────────────┐
   │    model     │  ←────  ML tam olarak burası
   └──────────────┘
          ↓
    10 sınıf skoru
```

Stage 1'den 4'e kadar yaptığın hiçbir şey öğrenmiyor. Aynı girdi her zaman aynı
çıktıyı veriyor ve kurallarını sen yazdın. İşin çoğunu bu kaplıyor.

Peki `model/train.py`'ı ML yapan ne? Elle kural yazsaydık şöyle olurdu:

```python
if "validate" in name:
    return "validator"
if outDegree > 4 and awaitCount > 2:
    return "orchestrator"
```

Bu çalışabilir — ama makine öğrenmesi değil, çünkü **hangi feature'ın ne kadar
önemli olduğuna sen karar verdin.** `> 4` eşiğini sen seçtin.

Logistic regression'da ise sadece örnekleri veriyorsun ve şu tablo veriden
çıkıyor:

```
name:validate       validator      için   +2.8
callee:save         orchestrator   için   +0.7
comparisonCount     domain_logic   için   +0.9
```

Bu tabloyu kimse yazmadı. Makine öğrenmesinin özü tam olarak bu.

Ve pratik sonucu: **öğrenme eğitimde bitiyor.** Çıkarım sırasında model hiçbir şey
öğrenmiyor, sadece donmuş `W` ve `b` ile çarpma-toplama yapıyor. Üretime giden
şeyin birkaç yüz KB'lık bir JSON dosyası olmasının sebebi bu — ne runtime, ne
model indirmesi, ne native bağımlılık.

---

## Sıradaki adım

```bash
make progress
```

Beş aşamayı ve hangisinin sırada olduğunu basar. Her aşamanın test dosyası, ne
yaptığını ve **neden** öyle yaptığını anlatan bir açıklamayla başlıyor.

Terimlerden takıldığın olursa: [`glossary.md`](glossary.md).
