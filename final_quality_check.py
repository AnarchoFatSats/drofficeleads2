#!/usr/bin/env python3
"""
VantagePoint CRM - Final Quality Assurance Check
Comprehensive review for syntax errors, professional polish, and best practices
"""

import os
import re
import json
from pathlib import Path

def check_html_issues():
    """Check HTML files for common issues"""
    issues = []
    html_files = ['aws_deploy/index.html', 'aws_deploy/login.html', 'aws_deploy/launcher.html']
    
    for file_path in html_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for common HTML issues
            if '<!DOCTYPE html>' not in content:
                issues.append(f"❌ {file_path}: Missing DOCTYPE declaration")
            
            if 'lang="en"' not in content:
                issues.append(f"❌ {file_path}: Missing language attribute")
            
            # Check for viewport meta tag
            if 'name="viewport"' not in content:
                issues.append(f"❌ {file_path}: Missing responsive viewport meta tag")
            
            # Check for proper title
            if '<title>' not in content or '<title></title>' in content:
                issues.append(f"❌ {file_path}: Missing or empty title tag")
            
            # Check for unclosed tags (basic check)
            div_open = content.count('<div')
            div_close = content.count('</div>')
            if div_open != div_close:
                issues.append(f"⚠️ {file_path}: Potential unclosed div tags ({div_open} open, {div_close} close)")
    
    return issues

def check_javascript_issues():
    """Check JavaScript for common issues"""
    issues = []
    html_files = ['aws_deploy/index.html', 'aws_deploy/login.html']
    
    for file_path in html_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract JavaScript content
            js_pattern = r'<script>(.*?)</script>'
            js_matches = re.findall(js_pattern, content, re.DOTALL)
            
            for js_content in js_matches:
                # Check for common JS issues
                if 'console.log' in js_content:
                    # Count debug logs (should be minimal in production)
                    log_count = js_content.count('console.log')
                    if log_count > 10:
                        issues.append(f"⚠️ {file_path}: Many console.log statements ({log_count}) - consider reducing for production")
                
                # Check for proper error handling
                if 'try {' in js_content and 'catch' not in js_content:
                    issues.append(f"❌ {file_path}: Try block without catch - potential unhandled errors")
                
                # Check for async/await best practices
                if 'async function' in js_content and 'await' not in js_content:
                    issues.append(f"⚠️ {file_path}: Async function without await - potential promise issues")
    
    return issues

def check_css_issues():
    """Check CSS for professional styling issues"""
    issues = []
    recommendations = []
    
    html_files = ['aws_deploy/index.html']
    
    for file_path in html_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract CSS content
            css_pattern = r'<style>(.*?)</style>'
            css_matches = re.findall(css_pattern, content, re.DOTALL)
            
            for css_content in css_matches:
                # Check for CSS best practices
                if ':root' in css_content:
                    recommendations.append(f"✅ {file_path}: Good use of CSS custom properties")
                
                # Check for responsive design
                if '@media' in css_content:
                    recommendations.append(f"✅ {file_path}: Responsive design implemented")
                else:
                    issues.append(f"⚠️ {file_path}: No responsive breakpoints found")
                
                # Check for accessibility
                if ':focus' in css_content:
                    recommendations.append(f"✅ {file_path}: Focus states implemented for accessibility")
                else:
                    issues.append(f"⚠️ {file_path}: Missing focus states for accessibility")
                
                # Check for hover effects
                if ':hover' in css_content:
                    recommendations.append(f"✅ {file_path}: Interactive hover effects implemented")
    
    return issues, recommendations

def check_security_issues():
    """Check for security best practices"""
    issues = []
    recommendations = []
    
    # Check Lambda function for security
    lambda_file = 'lambda_function.py'
    if os.path.exists(lambda_file):
        with open(lambda_file, 'r') as f:
            content = f.read()
        
        # Check for password handling
        if 'password' in content.lower() and 'hash' in content:
            recommendations.append(f"✅ {lambda_file}: Password hashing implemented")
        
        # Check for SQL injection protection (not applicable here, but good practice)
        if 'jwt' in content.lower():
            recommendations.append(f"✅ {lambda_file}: JWT authentication implemented")
        
        # Check for CORS headers
        if 'Access-Control-Allow-Origin' in content:
            recommendations.append(f"✅ {lambda_file}: CORS headers configured")
        
        # Check for input validation
        if 'required' in content and 'validate' in content.lower():
            recommendations.append(f"✅ {lambda_file}: Input validation present")
    
    return issues, recommendations

def check_performance_issues():
    """Check for performance optimization"""
    issues = []
    recommendations = []
    
    html_files = ['aws_deploy/index.html']
    
    for file_path in html_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for CDN usage
            if 'cdn.jsdelivr.net' in content or 'cdnjs.cloudflare.com' in content:
                recommendations.append(f"✅ {file_path}: Using CDN for external libraries")
            
            # Check for font loading optimization
            if 'fonts.googleapis.com' in content and 'display=swap' in content:
                recommendations.append(f"✅ {file_path}: Font loading optimized with display=swap")
            
            # Check for image optimization (if any)
            img_count = content.count('<img')
            if img_count > 0:
                if 'loading="lazy"' not in content:
                    issues.append(f"⚠️ {file_path}: Consider lazy loading for images")
            
            # Check for minification opportunities
            file_size = len(content)
            if file_size > 100000:  # 100KB
                issues.append(f"⚠️ {file_path}: Large file size ({file_size} bytes) - consider minification")
    
    return issues, recommendations

def check_accessibility():
    """Check accessibility compliance"""
    issues = []
    recommendations = []
    
    html_files = ['aws_deploy/index.html', 'aws_deploy/login.html']
    
    for file_path in html_files:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for ARIA labels
            if 'aria-label' in content:
                recommendations.append(f"✅ {file_path}: ARIA labels implemented")
            
            # Check for alt tags on buttons with icons
            if '<i class="fas' in content and 'aria-hidden="true"' not in content:
                issues.append(f"⚠️ {file_path}: Consider aria-hidden='true' for decorative icons")
            
            # Check for semantic HTML
            if '<main>' in content or '<section>' in content:
                recommendations.append(f"✅ {file_path}: Semantic HTML elements used")
            
            # Check for form labels
            if '<input' in content:
                if 'label' in content:
                    recommendations.append(f"✅ {file_path}: Form labels present")
                else:
                    issues.append(f"❌ {file_path}: Missing form labels for accessibility")
    
    return issues, recommendations

def run_final_quality_check():
    """Run comprehensive quality check"""
    print("🔍 VantagePoint CRM - Final Quality Assurance Check")
    print("=" * 60)
    
    all_issues = []
    all_recommendations = []
    
    # Run all checks
    print("\n🔍 Checking HTML Structure...")
    html_issues = check_html_issues()
    all_issues.extend(html_issues)
    
    print("🔍 Checking JavaScript...")
    js_issues = check_javascript_issues()
    all_issues.extend(js_issues)
    
    print("🔍 Checking CSS & Styling...")
    css_issues, css_recs = check_css_issues()
    all_issues.extend(css_issues)
    all_recommendations.extend(css_recs)
    
    print("🔍 Checking Security...")
    sec_issues, sec_recs = check_security_issues()
    all_issues.extend(sec_issues)
    all_recommendations.extend(sec_recs)
    
    print("🔍 Checking Performance...")
    perf_issues, perf_recs = check_performance_issues()
    all_issues.extend(perf_issues)
    all_recommendations.extend(perf_recs)
    
    print("🔍 Checking Accessibility...")
    acc_issues, acc_recs = check_accessibility()
    all_issues.extend(acc_issues)
    all_recommendations.extend(acc_recs)
    
    # Print results
    print(f"\n📊 QUALITY CHECK RESULTS:")
    print(f"=" * 60)
    
    if not all_issues:
        print("🎉 NO CRITICAL ISSUES FOUND!")
    else:
        print(f"⚠️ ISSUES TO ADDRESS ({len(all_issues)}):")
        for issue in all_issues:
            print(f"   {issue}")
    
    if all_recommendations:
        print(f"\n✅ POSITIVE FINDINGS ({len(all_recommendations)}):")
        for rec in all_recommendations:
            print(f"   {rec}")
    
    # Overall assessment
    critical_issues = [i for i in all_issues if i.startswith('❌')]
    warnings = [i for i in all_issues if i.startswith('⚠️')]
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print(f"   Critical Issues: {len(critical_issues)}")
    print(f"   Warnings: {len(warnings)}")
    print(f"   Best Practices: {len(all_recommendations)}")
    
    if len(critical_issues) == 0 and len(warnings) <= 3:
        print(f"\n🏆 PRODUCTION READY!")
        print(f"   VantagePoint CRM meets professional quality standards")
    elif len(critical_issues) == 0:
        print(f"\n✅ GOOD QUALITY")
        print(f"   Minor improvements recommended but production ready")
    else:
        print(f"\n⚠️ NEEDS ATTENTION")
        print(f"   Address critical issues before production deployment")
    
    return len(critical_issues) == 0

if __name__ == "__main__":
    run_final_quality_check() 