# lxq_nnunet

Pretrained segmentation models and inference code for prediction of post-hepatectomy liver failure (PHLF).

This repository releases the automatic segmentation pipeline based on nnU-Net V2, providing precise voxel-wise segmentation of multiple organs.

------

## Highlights

This project leverages the nnU-Net deep learning framework to achieve precise segmentation of five target structures on contrast-enhanced abdominal MRI / CT:

1. Whole liver - Accurate liver parenchyma segmentation for volumetry
2. Liver Tumor - Automatic detection and segmentation of hepatic mass
3. Couinaud Liver Segments - Automatic segmentation of eight Couinaud liver segments classification
4. Spleen - Automatic segmentation of spleen
5. Skeletal Muscle - Precise psoas major muscle segmentation

The five segmentation outputs feed downstream FLR volumetry and function quantification, which in turn feed the PHLF prediction model. These models are trained and validated on the PHLF Database, a comprehensive clinical dataset designed for liver surgery planning and outcome prediction.

------

## Background

Predicting PHLF requires accurate, voxel-wise quantification of the future liver remnant (FLR) — its volume and (indirectly) its function. This in turn depends on reliable automatic segmentation of multiple abdominal organs.

------

## Pre-trained Models

All five trained models are released on Hugging Face:

🔗 https://huggingface.co/Xunqi/nnunet_segment_model/tree/main

| Task               | Configuration | Modality |
| ------------------ | ------------- | -------- |
| couinaud_segment   | `3d_fullres`  | MRI      |
| liver_segment      | `3d_fullres`  | MRI      |
| livertumor_segment | `3d_fullres`  | MRI      |
| Spleen_segment     | `3d_fullres`  | MRI      |
| muscle_segment     | `3d_fullres`  | MRI      |

To use a pre-trained model:

1. Download the model from the link above
2. Install it using:

```bash
nnUNetv2_install_pretrained_model_from_zip path/to/downloaded_model.zip
```

------

## Installation

```bash
conda create -n lxq_nnunet python=3.10 -y
conda activate lxq_nnunet
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -e .
```

Set the three nnU-Net environment variables:

```bash
export nnUNet_raw=/path/to/nnUNet_raw
export nnUNet_preprocessed=/path/to/nnUNet_preprocessed
export nnUNet_results=/path/to/nnUNet_results
```

------

## Inference with Pretrained Models

```bash
# 1) Download the desired model from Hugging Face and unzip into $nnUNet_results
# 2) Run prediction:
nnUNetv2_predict \
    -i  /path/to/input_nifti \
    -o  /path/to/output \
    -d  <DatasetID> \
    -c  3d_fullres \
    -f  all
```

------

## Reproducing Training from Scratch

Data must follow the nnU-Net v2 format:

```bash
nnUNetv2_plan_and_preprocess -d <DatasetID> --verify_dataset_integrity
nnUNetv2_train <DatasetID> 3d_fullres <fold>
```

------

## PHLF Database (Companion Dataset)

The annotated dataset used to train these models — and used for PHLF prediction in our study — includes:

| Item                 | Description                                                  |
| -------------------- | ------------------------------------------------------------ |
| Imaging modality     | hepatobiliary phase (HBP)                                    |
| Annotated structures | liver, liver tumor, 8 Couinaud segments, spleen, skeletal muscle |
| Annotation protocol  | nnU-Net pre-segmentation → manual correction by two radiologists |

------

## Ground-Truth Annotation Protocol

Ground-truth labels in our dataset were produced through a rigorous semi-automatic pipeline:

1. Five initial nnU-Net models—specifically, those for liver parenchyma segmentation, liver segment delineation, hepatic tumor segmentation, spleen segmentation, and psoas major muscle segmentation—were trained on a small, manually annotated dataset subset.
2. The models produced first-pass predictions on the remaining cases
3. These preliminary outputs underwent a comprehensive two-tiered manual review process. First, a radiologist with 5 years of experience refined the AI-generated segmentations. Subsequently, a senior abdominal radiologist with 15 years of expertise conducted a final quality check and performed additional refinements as required. The resulting consensus annotations, representing clinically adjudicated ground truth labels, are provided.

This semi-automatic pipeline enabled efficient annotation across all five structures. The released models in this repository are trained on the final, radiologist-corrected labels, ensuring high-quality ground truth for accurate segmentation.

------

## Project Structure

```
lxq_nnunet/
├── nnunetv2/
│   ├── experiment_planning/    # Dataset fingerprinting and planning
│   ├── inference/              # Inference and prediction modules
│   ├── model_sharing/          # Model download/export utilities
│   ├── paths.py                # Path configuration
│   ├── postprocessing/         # Post-processing utilities
│   ├── run/                    # Training entry points
│   ├── training/               # Training logic and trainers
│   │   ├── data_augmentation/  # Data augmentation transforms
│   │   ├── dataloading/        # Data loading utilities
│   │   ├── loss/               # Loss functions
│   │   ├── lr_scheduler/       # Learning rate schedulers
│   │   └── nnUNetTrainer/      # Trainer implementations
│   └── utilities/              # Utility functions
├── documentation/              # Documentation and examples
├── pyproject.toml              # Project configuration
└── setup.py                    # Setup script
```

------

## License

- The nnU-Net framework code retains its original Apache-2.0 license.
- Our released model weights and dataset are distributed under Apache-2.0.

------

## Citation



------

## Acknowledgments

This project is based on the nnU-Net framework developed by the Division of Medical Image Computing at the German Cancer Research Center (DKFZ), Heidelberg, Germany. We thank Fabian Isensee and the DKFZ team for releasing nnU-Net.

We extend our sincere gratitude to Dr. X.Z. and Dr D.K. who provided high-quality ground truth annotations for all five segmentation targets. Their expertise and meticulous manual delineations — through nnU-Net pre-segmentation followed by careful manual correction — form the foundation of the accurate segmentation models in this project.

We also acknowledge the PHLF Database, a dedicated clinical dataset that supports the development and validation of liver-related segmentation algorithms, enabling advances in preoperative planning and postoperative outcome prediction for hepatic surgery.
