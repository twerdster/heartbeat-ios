// Minimal macOS stand-in for the single UIKit type used by the original
// Algorithm.{h,mm}: UIColor with colorWithRed:green:blue:alpha: and
// getRed:green:blue:alpha:. This is new harness code, not original source.
// It exists only so the unmodified original Algorithm.mm can be compiled and
// executed on macOS as a reference ("golden") implementation.
#pragma once
#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>

@interface UIColor : NSObject
+ (instancetype)colorWithRed:(CGFloat)red green:(CGFloat)green blue:(CGFloat)blue alpha:(CGFloat)alpha;
- (BOOL)getRed:(CGFloat *)red green:(CGFloat *)green blue:(CGFloat *)blue alpha:(CGFloat *)alpha;
@end
