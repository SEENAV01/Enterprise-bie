# Navin's script for the Q14 film (20 November 2026)

Navin edited the narration of the third Q14 film (VM run `studio-photosynthesis-q14-place`) in the Claude Doc "Q14 film:
teacher ki narration script" and sent it back. In his words, the aim: "sentence pura lage, teacher jaisa lage, aisa na
lage koi ek flow mein machine paragraph padh rahi hai; BIE ko seekhane ke liye edit ki hai, taaki isse seekh le ki teacher
video ko explain kaise karta hai." On the card he chose to try both ways: the film made with his own lines, and BIE writing
fresh in his way.

His lines as he typed them (spelling as typed). A NOTE is the part of his cell that speaks to BIE, not a line to say.

| # | His line | Note |
| --- | --- | --- |
| 1.1 | Patte mein jama protons ko ek khaas exit milte hi ATP kaise banne lagta hai?aayiye jaante hai |  |
| 1.2 | Par pehale Proton gradient mein itni dilchaspi kyun  iski wajah jaan lete hai - aisa isiliye hai kyuki iske ghatne se ATP banane ki energy milti hai. | Yha par kyu aur kyunki mein overlap ho jata hai jiski vajah se artificial lagta hai sab kuchh yeh words jodke wo bhed kiya ja sakta hai |
| 2.1 | Aayiye is process se judi Pehle jagah pehchaan lete hain : leaf ki is mesophyll cell ke chloroplast mein photosynthesis hota hai. |  |
| 2.2 | Dhoop yahan pahunchti hai; ab isi chloroplast ke andar chalte hain. Aur cheejon ko aur detail mein samjhte hai |  |
| 3.1 | Chloro plast kevandar Yeh thylakoid band chapti thaili jaisa dikhta  hai; jiske andar lumen aur bahar stroma hai. |  |
| 3.2 | Dhoop ki energy kaam aati hai, par ek sawal ab bhi banta hai ki  band membrane kyun chahiye— iska seedha sa jawab h hai protons ka jamav bachane ke liye; ab chaliye thoda aur  paas se dekhte hsi |  |
| 4.1 | Proton pump ko aap motor samjhiye yeh energy lagaakar H+ ko membrane ke paar stroma se lumen mein pahunchata hai. |  |
| 4.2 | Jisse Andar H+ ki concentration zyadanho jaati hai ,aur  bahar kam— jiske jaran thylakoid membrane ke across yahi proton gradient ban jata hai theek baterry ke higher potiential lower potential | meri instruction tumne membrane ko ek baandh ke exapmle se btaya tha shayad pehale wali video mein wo sahi tha |
| 4.3 | Ab sawal banta hai ikkathe huye  H+ wapas kaise niklein— isme kaam aata hai  ATP synthase ka khaas raasta jo gradient ki energy se ATP banwata hai. |  |
| 5.1 | ATP synthase ke do parts dekho: membrane mein dhansa CF0 H+ ko channel se paar jaane deta hai—yeh facilitated diffusion hai. |  |
| 5.2 | Doosra part CF1 bahar stroma ki taraf nikla hai; ADP aur Pi isi catalytic hisse tak aate hain. |  |
| 5.3 | H+ lumen se CF0 ke transmembrane channel se stroma mein lautte hain, jisse gradient ghatta hai; ATPase ka F0 bhi isi part ka naam hai. |  |
| 5.4 | Par gor krne wali baat h H+ ke flow se ATP kyun banta hai—dekhiye hita kya hai gradient ki released energy CF1 mein conformational change, yaani shape change, chalati hai; ab jiske karan  ADP aur Pi ke milne se ATP banta hai. |  |
| 5.5 | CF1 baar-baar ADP aur Pi se several molecules of energy-packed ATP banata hai—dekhiye kaise gradient ka breakdown ab usable chemical energy de raha hai. |  |
| 6.1 | Agar membrane mein leak ho, toh kya har nikalta H+ ATP banayega—dekho, yeh H+ ATP synthase ko bypass kar raha hai. |  |
| 6.2 | Nahi; leak se lautte H+ gradient ki energy waste karte hain, CF1 ko ATP banane ke liye yeh energy nahi milti. |  |
| 6.3 | Isliye chemiosmosis ko chaar cheezein saath chahiye: intact membrane, proton pump, proton gradient aur ATP synthase. |  |
| 7.1 | Ab sahi chalti membrane par bana ATP stroma mein aata hai; electron movement se bana NADPH bhi biosynthetic reactions ko turant supply hota hai. |  |
| 7.2 | Akhir inki  zaroorat hai kyun—CO2 fixation ke baad carbon ko sugar banane laayak badalna hai; pehle CO2 ko RuBP pakadta hai aur do 3-PGA bante hain. |  |
| 7.3 | Ab ATP energy deta hai aur NADPH reducing power; kai reactions mein dono kharch hote hain aur 3-PGA se G3P banta hai. |  |
| 7.4 | G3P ka kuch hissa aage kai reactions se sugar banata hai—do teen-carbon units ka carbon ek chhe-carbon glucose mein aa sakta hai. |  |
| 7.5 | Is videk se aapko yeh baatein Yaad rakhni hai : H+ ka CF0 se return, CF1 ka shape change aur ATP—phir stroma mein NADPH ke saath sugar-making. |  |

The six ways BIE took from these lines are in `bie/brain/studio_film.py` ("A TEACHER EXPLAINING, NOT A MACHINE
READING A PARAGRAPH") and its code checks (`teacher_problems`).
