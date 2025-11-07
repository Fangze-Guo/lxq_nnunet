import os
import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd
import json

def get_image_orientation(affine):
    """从仿射矩阵获取图像方向"""
    orient = ''
    for i in range(3):
        if np.argmax(np.abs(affine[:3, i])) == 0:
            orient += 'R' if affine[0, i] > 0 else 'L'
        elif np.argmax(np.abs(affine[:3, i])) == 1:
            orient += 'A' if affine[1, i] > 0 else 'P'
        else:
            orient += 'S' if affine[2, i] > 0 else 'I'
    return orient

def check_rigid_registration_requirements(file1_path, file2_path):
    """
    检查两个文件是否符合刚性配准要求
    返回检查结果字典
    """
    try:
        # 加载图像
        img1 = nib.load(file1_path)
        img2 = nib.load(file2_path)
        
        # 获取基本信息
        data1 = img1.get_fdata()
        data2 = img2.get_fdata()
        
        # 获取方向
        orient1 = ''.join(nib.aff2axcodes(img1.affine))
        orient2 = ''.join(nib.aff2axcodes(img2.affine))
        
        # 获取物理空间信息
        spacing1 = img1.header.get_zooms()[:3]
        spacing2 = img2.header.get_zooms()[:3]
        
        # 获取图像尺寸
        shape1 = data1.shape
        shape2 = data2.shape
        
        # 计算物理尺寸 (mm)
        physical_size1 = [shape1[i] * spacing1[i] for i in range(3)]
        physical_size2 = [shape2[i] * spacing2[i] for i in range(3)]
        
        # 计算物理尺寸差异百分比
        size_diff_percent = [abs(physical_size1[i] - physical_size2[i]) / ((physical_size1[i] + physical_size2[i]) / 2) * 100 for i in range(3)]
        max_size_diff = max(size_diff_percent)
        
        # 检查项目
        checks = {
            '文件1': str(file1_path),
            '文件2': str(file2_path),
            '文件名': file1_path.name,
            '方向一致性': {
                '文件1方向': orient1,
                '文件2方向': orient2,
                '是否一致': orient1 == orient2,
                '状态': '✅' if orient1 == orient2 else '⚠️'
            },
            '体素间距': {
                '文件1间距': f"{spacing1[0]:.3f}×{spacing1[1]:.3f}×{spacing1[2]:.3f} mm",
                '文件2间距': f"{spacing2[0]:.3f}×{spacing2[1]:.3f}×{spacing2[2]:.3f} mm", 
                '是否一致': spacing1 == spacing2,
                '状态': '✅' if spacing1 == spacing2 else '⚠️'
            },
            '物理尺寸相似性': {
                '文件1物理尺寸': f"{physical_size1[0]:.1f}×{physical_size1[1]:.1f}×{physical_size1[2]:.1f} mm",
                '文件2物理尺寸': f"{physical_size2[0]:.1f}×{physical_size2[1]:.1f}×{physical_size2[2]:.1f} mm",
                '尺寸差异百分比': size_diff_percent,
                '最大差异': f"{max_size_diff:.1f}%",
                '状态': '✅' if max_size_diff < 10 else '⚠️'  # 10% 阈值
            },
            '图像尺寸': {
                '文件1尺寸': shape1,
                '文件2尺寸': shape2, 
                '是否一致': shape1 == shape2,
                '状态': '❌' if shape1 != shape2 else '✅'
            }
        }
        
        # 总体评估
        orientation_ok = orient1 == orient2
        spacing_ok = spacing1 == spacing2
        physical_size_ok = max_size_diff < 10  # 10% 差异阈值
        
        if orientation_ok and spacing_ok and physical_size_ok:
            overall_status = '优秀'
            overall_score = 5
        elif orientation_ok and physical_size_ok:
            overall_status = '良好'
            overall_score = 4
        elif physical_size_ok:
            overall_status = '一般'
            overall_score = 3
        else:
            overall_status = '较差'
            overall_score = 2
            
        checks['总体评估'] = {
            '状态': overall_status,
            '得分': overall_score,
            '描述': f'{overall_status} - {get_assessment_description(overall_status)}'
        }
        
        # 问题分析
        issues = []
        if not orientation_ok:
            issues.append(f"方向不一致: {orient1} vs {orient2}")
        if not spacing_ok:
            issues.append("体素间距不一致")
        if not physical_size_ok:
            issues.append(f"物理尺寸差异过大 (最大{max_size_diff:.1f}%)")
            
        checks['问题列表'] = issues
        checks['问题数量'] = len(issues)
            
        return checks
        
    except Exception as e:
        return {
            '文件1': str(file1_path),
            '文件2': str(file2_path),
            '文件名': file1_path.name,
            '错误': str(e),
            '总体评估': {'状态': '错误', '得分': 1, '描述': f'检查失败: {str(e)}'},
            '问题列表': [f'文件读取错误: {str(e)}'],
            '问题数量': 1
        }

def get_assessment_description(status):
    """获取评估描述"""
    descriptions = {
        '优秀': '完全符合刚性配准要求，可直接进行配准',
        '良好': '符合刚性配准要求，建议统一方向',
        '一般': '可以进行刚性配准但建议预处理',
        '较差': '需要预处理后才能进行刚性配准',
        '错误': '文件检查失败'
    }
    return descriptions.get(status, '未知状态')

def analyze_poor_files(dir1_path, dir2_path):
    """
    专门分析较差的文件
    """
    dir1 = Path(dir1_path)
    dir2 = Path(dir2_path)
    
    if not dir1.exists():
        print(f"❌ 目录1不存在: {dir1_path}")
        return []
    if not dir2.exists():
        print(f"❌ 目录2不存在: {dir2_path}")
        return []
    
    # 获取两个目录中的nii.gz文件
    files1 = {f.name: f for f in dir1.glob("*.nii.gz")}
    files2 = {f.name: f for f in dir2.glob("*.nii.gz")}
    
    common_files = set(files1.keys()) & set(files2.keys())
    
    print(f"📁 目录1: {dir1_path}")
    print(f"📁 目录2: {dir2_path}")
    print(f"📊 共同文件数量: {len(common_files)}")
    print("=" * 80)
    
    if not common_files:
        print("❌ 没有找到共同的文件")
        return []
    
    poor_files = []
    all_results = []
    
    for filename in sorted(common_files):
        print(f"🔍 检查: {filename}")
        
        file1_path = files1[filename]
        file2_path = files2[filename]
        
        result = check_rigid_registration_requirements(file1_path, file2_path)
        all_results.append(result)
        
        if result['总体评估']['状态'] in ['较差', '错误']:
            poor_files.append(result)
            print(f"❌ 添加到较差文件列表")
        else:
            print(f"✅ 符合要求")
    
    return poor_files, all_results

def generate_poor_files_report(poor_files, output_dir="."):
    """
    生成较差文件的详细报告
    """
    if not poor_files:
        print("🎉 没有较差的文件！所有文件都符合刚性配准要求。")
        return
    
    print(f"\n{'='*80}")
    print(f"📋 较差文件报告 - 共 {len(poor_files)} 个文件需要关注")
    print(f"{'='*80}")
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 详细分析每个较差文件
    for i, file_info in enumerate(poor_files, 1):
        print(f"\n{'#'*60}")
        print(f"#{i} 问题文件: {file_info['文件名']}")
        print(f"{'#'*60}")
        
        print(f"📄 文件路径:")
        print(f"   文件1: {file_info['文件1']}")
        print(f"   文件2: {file_info['文件2']}")
        
        print(f"\n📊 评估结果: {file_info['总体评估']['描述']}")
        
        print(f"\n🔍 具体问题:")
        for issue in file_info.get('问题列表', []):
            print(f"   ❌ {issue}")
        
        print(f"\n📈 详细检查结果:")
        for check_name, check_data in file_info.items():
            if check_name in ['文件1', '文件2', '文件名', '总体评估', '问题列表', '问题数量', '错误']:
                continue
                
            print(f"   {check_data.get('状态', '❓')} {check_name}:")
            for key, value in check_data.items():
                if key not in ['状态']:
                    print(f"      {key}: {value}")
    
    # 生成统计信息
    generate_poor_files_statistics(poor_files, output_path)
    
    # 保存详细报告到文件
    save_detailed_report(poor_files, output_path)

def generate_poor_files_statistics(poor_files, output_path):
    """
    生成较差文件的统计信息
    """
    print(f"\n{'='*80}")
    print(f"📈 较差文件统计分析")
    print(f"{'='*80}")
    
    # 问题类型统计
    issue_types = {}
    for file_info in poor_files:
        for issue in file_info.get('问题列表', []):
            issue_type = issue.split(':')[0] if ':' in issue else issue
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
    
    print(f"\n🔧 问题类型分布:")
    for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(poor_files)) * 100
        print(f"   {issue_type}: {count} 个文件 ({percentage:.1f}%)")
    
    # 问题数量统计
    issue_counts = {}
    for file_info in poor_files:
        issue_count = file_info.get('问题数量', 0)
        issue_counts[issue_count] = issue_counts.get(issue_count, 0) + 1
    
    print(f"\n🔢 问题数量分布:")
    for count, file_count in sorted(issue_counts.items()):
        percentage = (file_count / len(poor_files)) * 100
        print(f"   {count} 个问题: {file_count} 个文件 ({percentage:.1f}%)")

def save_detailed_report(poor_files, output_path):
    """
    保存详细报告到文件
    """
    report_file = output_path / "poor_files_detailed_report.json"
    
    # 转换为可序列化的格式
    serializable_report = []
    for file_info in poor_files:
        serializable_info = {}
        for key, value in file_info.items():
            if isinstance(value, (np.ndarray, np.generic)):
                serializable_info[key] = value.tolist() if hasattr(value, 'tolist') else str(value)
            elif hasattr(value, '__dict__'):
                serializable_info[key] = str(value)
            else:
                serializable_info[key] = value
        serializable_report.append(serializable_info)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 详细报告已保存至: {report_file}")
    
    # 生成简化的CSV报告
    csv_report = []
    for file_info in poor_files:
        csv_row = {
            '文件名': file_info['文件名'],
            '评估状态': file_info['总体评估']['状态'],
            '问题数量': file_info.get('问题数量', 0),
            '主要问题': '; '.join(file_info.get('问题列表', [])),
            '方向一致性': file_info.get('方向一致性', {}).get('状态', '未知'),
            '体素间距': file_info.get('体素间距', {}).get('状态', '未知'),
            '物理尺寸': file_info.get('物理尺寸相似性', {}).get('状态', '未知')
        }
        csv_report.append(csv_row)
    
    csv_file = output_path / "poor_files_summary.csv"
    df = pd.DataFrame(csv_report)
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    
    print(f"📊 摘要报告已保存至: {csv_file}")

def generate_fix_recommendations(poor_files):
    """
    为较差文件生成修复建议
    """
    print(f"\n{'='*80}")
    print(f"🔧 修复建议")
    print(f"{'='*80}")
    
    for i, file_info in enumerate(poor_files, 1):
        print(f"\n📄 文件: {file_info['文件名']}")
        print(f"   问题: {', '.join(file_info.get('问题列表', []))}")
        
        recommendations = []
        
        # 根据问题类型生成建议
        for issue in file_info.get('问题列表', []):
            if "方向不一致" in issue:
                recommendations.append("使用方向调整函数统一方向 (如reorient_to_lps)")
            if "体素间距不一致" in issue:
                recommendations.append("使用物理空间重采样统一体素间距")
            if "物理尺寸差异过大" in issue:
                recommendations.append("检查扫描范围，可能需要调整配准策略")
            if "文件读取错误" in issue:
                recommendations.append("检查文件完整性，重新转换DICOM")
        
        if recommendations:
            print("   建议修复步骤:")
            for rec in set(recommendations):  # 去重
                print(f"     ✅ {rec}")
        else:
            print("   暂无具体修复建议")

def main():
    """
    主函数 - 专门分析较差的文件
    """
    # 设置目录路径
    dir1_path = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/precontrast/dicom_to_nii"
    dir2_path = "/media/dell/T7 Shield/nnunet/AllData/HK/finished/HBP/HBP_nii_lps"
    
    print("🎯 刚性配准要求检查 - 较差文件分析")
    print("=" * 60)
    
    # 分析较差的文件
    poor_files, all_results = analyze_poor_files(dir1_path, dir2_path)
    
    if poor_files:
        # 生成报告
        generate_poor_files_report(poor_files)
        
        # 生成修复建议
        generate_fix_recommendations(poor_files)
        
        # 总体统计
        total_files = len(all_results)
        poor_count = len(poor_files)
        
        print(f"\n{'='*80}")
        print(f"📈 最终统计")
        print(f"{'='*80}")
        print(f"总文件数: {total_files}")
        print(f"较差文件: {poor_count} ({poor_count/total_files*100:.1f}%)")
        print(f"合格文件: {total_files - poor_count} ({(total_files-poor_count)/total_files*100:.1f}%)")
        
        if poor_count / total_files > 0.5:
            print(f"\n⚠️  警告: 超过50%的文件需要预处理！")
            print(f"   建议批量预处理后再进行配准")
        else:
            print(f"\n✅ 大部分文件可以直接进行配准")
            
    else:
        print(f"\n🎉 恭喜！所有文件都符合刚性配准要求！")

if __name__ == "__main__":
    main()