# SpineNerveModelGenerator

A script to generate lumbosacral spine model with spinal nerve root structure.

# Abstract
Spinal cord injury (SCI) profoundly affects an individual's ability to move. Fortunately, recent advancements in neuromodulation, particularly the spatio-temporal epidural electrical stimulation (EES) targeting the spine nerve roots, promoted rapid rehabilitation of SCI patients. Such neuromodulation techniques require precise anatomical modelling of spinal cord. However, the lack of spine imaging datasets, especially high-quality magnetic resonance imaging (MRI) datasets highlighting nerve roots, hinders the translation of EES into medical practice. To address this problem, we introduce an open-access lumbosacral spine MRI dataset acquired in 14 healthy adults, using constructive interference in steady state (CISS) sequence, double echo steady state (DESS) sequence, and T2-weight turbo spin echo (T2-TSE) sequence, with enhanced nerve root resolution. The dataset also includes the corresponding anatomical annotations of nerve roots and the final reconstructed 3D spinal cord model. The quality of our dataset is assessed using image quality metrics implemented in MRI quality control tool (MRIQC). Our dataset provides a valuable platform to promote a wide range of spinal cord neuromodulation research and collaboration among neurorehabilitation engineers. 

# Requirements

-python=3.11.9 \
-bpy=4.1.0 \
-pyvista=0.44.0 \
-scipy=1.14.0 \
-pandas=2.2.2

The detailed requirements are listed in [env_requirements.yaml](env_requirements.yaml), the virtual envirionment can be created directly by execute: `conda env create -f env_requirement.yaml`

# Set Up
```
$ conda create -n Smgenv python=3.11
$ pip install bpy
$ pip install pyvista[all]
$ pip install pandas
$ pip install scipy
```

# Usage Example

An example of processing sub-02 annotions and creating models was in [Meshing Example](example.ipynb)
