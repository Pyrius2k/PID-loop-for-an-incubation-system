# 🌡️ PID Loop for an Incubation System  

> A master’s thesis project focused on developing a **PID (Proportional-Integral-Derivative) control loop** to maintain a stable temperature within a custom-built incubation system.  
> Designed for applications such as **biological experiments** and **quantum microscopy** (NV centers in diamond), enabling **long-term cultivation and observation of tissue samples** under physiological conditions.  

---

## 📑 Table of Contents  
- [✨ Project Highlights](#-project-highlights)  
- [⚙️ Engineering & Simulation](#️-engineering--simulation)  
- [🔬 Biological Samples](#-biological-samples)  
- [📊 Performance & Data](#-performance--data)  
- [💡 Project Overview & Challenges](#-project-overview--challenges)  
- [🔮 Outlook](#-outlook)  
- [🛠️ Tech Stack](#️-tech-stack)  

---

## ✨ Project Highlights  
- PID-based temperature control using **Arduino**  
- Designed for integration into **wide-field NV quantum microscopes**  
- Enables **cultivation & imaging** of colon precision-cut tissue slices (PCTS)  
- Validated with **brightfield imaging** and **histological staining**  

---

## ⚙️ Engineering & Simulation  

📌 The incubation system was designed for stable integration with a microscope.  

- **Incubator design** (CAD render):  
  <img src="https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/incubator.png" width="55%">  

- **NV Center lattice (quantum sensor component):**  
  <img src="https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/nv.png" width="35%">  

- **Temperature distribution (COMSOL simulation):**  
  <img src="https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/tdistribution.png" width="50%">  

---

## 🔬 Biological Samples  

✅ **Colon PCTS cultivation tests** to verify:  
- Biocompatibility of system materials  
- Maintenance of cell vitality  

| Brightfield Microscopy | H&E Staining |
|------------------------|--------------|
| <img src="https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/brightfield.png" width="60%"> | <img src="https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/colon_he.png" width="60%"> |

---

## 📊 Performance & Data  

- PID control implemented on **Arduino**  
- Provides precise temperature stabilization  

![PID Graph](https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/pidgraph.png)  

> The results demonstrate stable temperature regulation, maintaining defined physiological conditions.  

---

## 💡 Project Overview & Challenges  

- Development of **incubation chamber**, **gas mixing system**, **humidifier**, and **temperature control**  
- Integration into **wide-field NV quantum microscope**  
- Cultivation experiments with colon tissue in **Experimental Tumor Pathology lab**  
- Verification via microscopy imaging  

---

## 🔮 Outlook  

Next steps include:  
- Cultivation of **single-cell suspensions**  
- Focus on **HT29 colon tumor cell line** → studying peritoneal metastasis  
- **Long-term cell behavior tracking** over several days  
- Final goal: **seamless integration into microscope** for accurate, stable biological imaging  

---

## 🛠️ Tech Stack  

- **Languages**: Python (50.4%), C++ (49.6%)  
- **Platform**: Arduino-based PID control  
- **Tools**: COMSOL, wide-field microscopy, NV-based sensing  

---

✨ *This project demonstrates the feasibility of maintaining physiological conditions for colon tissue samples in a custom incubation system integrated with advanced quantum microscopy.*  
