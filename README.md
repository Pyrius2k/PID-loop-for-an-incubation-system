# 🌡️ PID Loop for an Incubation System

This repository contains the documentation and core files for a project focused on developing and implementing a **PID (Proportional-Integral-Derivative) control loop** to maintain a stable temperature within a custom-built incubation system. The system is designed for a variety of applications, including biological experiments that require precise thermal control, particularly for integration into wide-field microscopes utilizing nitrogen-vacancy (NV) centers in diamond. The objective is to enable the long-term cultivation and observation of biological samples, such as precision-cut tissue slices (PCTS) of the colon, under physiological conditions directly at the microscope.

## ✨ Project Visuals and Results

The following images provide a visual overview of the project, from the design and components to the final results.

### ⚙️ Engineering and Simulation

The project involved the conception and development of an incubation system tailored for integration into a wide-field microscope. This required careful design and simulation to ensure optimal performance.

A rendered CAD model of the incubator, showcasing its physical design.
<img src="https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/incubator.png" width="50%">
<br>
<img src="https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/nv.png" width="30%">
<br>
This image shows the lattice of a nitrogen-vacancy (NV) center, a key component in the quantum microscope system used for NV-based sensing.
<br>
A COMSOL simulation illustrating the temperature distribution within the incubator, vital for ensuring stable physiological conditions.
<img src="https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/tdistribution.png" width="40%">
<br>

### 🔬 Biological Samples

Experiments included cultivation tests of colon PCTS to verify biocompatibility and cell vitality. Bright-field microscopy images were acquired using the wide-field microscope to visualize the tissue structure.

This is a brightfield image of a mouse colon captured using our quantum microscope, showcasing the detailed tissue structure.
![bf Image](https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/brightfield.png)
<br>
![he Image](https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/colon_he.png)
<br>
This image shows the same mouse colon after staining, allowing for the clear visualization of layers like the serosa and mucosa, confirming cell vitality within the developed system.
<br>

### 📊 Performance and Data

The temperature control system employs a PID controller based on an Arduino, ensuring precise regulation.

![pid Image](https://github.com/Pyrius2k/PID-loop-for-an-incubation-system/blob/main/pidgraph.png)
<br>
The results of the PID control loop, showing how the system stabilizes the temperature over time and maintains defined physiological conditions.
<br>

## 💡 Project Overview and Challenges

This master’s thesis addresses the conception and development of an incubation system specifically designed for integration into a wide-field microscope utilizing nitrogen-vacancy (NV) centers in diamond. The objective is to enable the long-term cultivation and observation of biological samples, particularly precision-cut tissue slices (PCTS) of the colon, under physiological conditions directly at the microscope.

Within the scope of this work, the theoretical principles of cell cultivation and NV-based sensing are explained, and the requirements for such an incubation system are defined. Subsequently, various system components are constructed and tested, including a custom-built incubation chamber, a gas mixing system, a humidifier, and a temperature control system employing a PID controller based on an Arduino.

The experiments include cultivation tests of colon PCTS in the biology laboratory of the Experimental Tumor Pathology department to verify the biocompatibility of the materials used and the maintenance of cell vitality within the developed system. Furthermore, bright-field microscopy images of the tissue slices are acquired using the wide-field microscope to visualize the tissue structure.

## 🔬 Outlook

Building upon this, the optimized approach will be pursued and developed further. Upon successful cultivation and long-term observation of tissue sections, the cultivation of single-cell suspensions is planned. Specifically, the HT29 colon tumor cell line, which leads to peritoneal metastasis when applied to the serosal side, will be used for this purpose.

This work demonstrates the feasibility of cultivating mouse colon tissue sections while maintaining the required atmosphere. The ultimate goal of this project is the optimal integration of the incubation system into the wide-field microscope, so that the planned approach can resolve the observed problems and thus enable highly accurate long-term observations on individual cells. Longer observation periods are also a goal here to be able to observe cell behavior over several days.
