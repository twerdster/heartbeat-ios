// New 2026 native replay interface. Recorded PPG, not camera capture.
#import <TargetConditionals.h>
#if TARGET_OS_IPHONE
#import <UIKit/UIKit.h>
#define ViewBase UIView
#define Color UIColor
#define Font UIFont
#else
#import <Cocoa/Cocoa.h>
#define ViewBase NSView
#define Color NSColor
#define Font NSFont
#endif
#include "heartbeat_core.hpp"
#include <fstream>
#include <sstream>
#include <memory>
@interface HBView:ViewBase {std::vector<double> values,history; std::unique_ptr<HeartbeatCore> core; HBTrace trace; NSUInteger position; BOOL paused,synthetic,outputSaved; NSString*saveError; NSString*inputError; NSTimer*timer; NSTimeInterval lastSaveAttempt;}
-(void)resetRun;-(void)tick;-(void)toggle;-(void)changeInput;
@end
@implementation HBView
#if !TARGET_OS_IPHONE
-(BOOL)isFlipped{return YES;}
#endif
-(instancetype)initWithFrame:(CGRect)frame{if((self=[super initWithFrame:frame])){
#if TARGET_OS_IPHONE
 self.backgroundColor=[Color colorWithRed:.035 green:.055 blue:.09 alpha:1];
#endif
 NSString*p=[[NSBundle mainBundle]pathForResource:@"bidmc01-ppg" ofType:@"csv"];if(p){std::ifstream f(p.UTF8String);std::string line;getline(f,line);if(line=="sample"){try{while(getline(f,line)){if(!line.empty()){size_t used=0;double x=std::stod(line,&used);if(used!=line.size()||!std::isfinite(x)||x<0||x>1)throw std::runtime_error("Invalid PPG sample");values.push_back(x);}}}catch(...){values.clear();}}}if(values.empty())inputError=@"Bundled PPG input is missing or invalid";
 [self resetRun];timer=[NSTimer scheduledTimerWithTimeInterval:1./30 target:self selector:@selector(tick) userInfo:nil repeats:YES];
 NSArray*names=@[@"Pause",@"Restart",@"Switch input"];for(int i=0;i<3;++i){
#if TARGET_OS_IPHONE
 UIButton*b=[UIButton buttonWithType:UIButtonTypeSystem];[b setTitle:names[i] forState:UIControlStateNormal];b.titleLabel.font=[Font systemFontOfSize:15 weight:UIFontWeightSemibold];b.backgroundColor=[Color colorWithWhite:.15 alpha:1];b.layer.cornerRadius=8;[b addTarget:self action:i==0?@selector(toggle):i==1?@selector(resetRun):@selector(changeInput) forControlEvents:UIControlEventTouchUpInside];
#else
 NSButton*b=[NSButton buttonWithTitle:names[i] target:self action:i==0?@selector(toggle):i==1?@selector(resetRun):@selector(changeInput)];b.bezelStyle=NSBezelStyleRounded;
#endif
 b.tag=100+i;[self addSubview:b];}
 }return self;}
-(void)resetRun{core=std::make_unique<HeartbeatCore>();position=0;history.clear();trace={};paused=NO;outputSaved=NO;saveError=(!synthetic&&inputError)?inputError:nil;lastSaveAttempt=0;
#if TARGET_OS_IPHONE
[(UIButton*)[self viewWithTag:100] setTitle:@"Pause" forState:UIControlStateNormal];
#else
[(NSButton*)[self viewWithTag:100] setTitle:@"Pause"];
#endif
#if TARGET_OS_IPHONE
 UIApplication.sharedApplication.idleTimerDisabled=YES;
#endif
[self redraw];}
-(void)toggle{paused=!paused;
#if TARGET_OS_IPHONE
 UIApplication.sharedApplication.idleTimerDisabled=!paused&&position<(synthetic?900:values.size());
#endif

#if TARGET_OS_IPHONE
 [(UIButton*)[self viewWithTag:100] setTitle:paused?@"Resume":@"Pause" forState:UIControlStateNormal];
#else
 [(NSButton*)[self viewWithTag:100] setTitle:paused?@"Resume":@"Pause"];
#endif
 [self redraw];}
-(void)changeInput{synthetic=!synthetic;[self resetRun];}
-(void)redraw{
#if TARGET_OS_IPHONE
 [self setNeedsDisplay];
#else
 [self setNeedsDisplay:YES];
#endif
}
-(void)tick{if(!synthetic&&inputError)return;if(paused)return;if(position>=(synthetic?900:values.size())){if(!outputSaved&&NSDate.timeIntervalSinceReferenceDate-lastSaveAttempt>=1){[self saveState];[self redraw];}return;}if(!paused&&position<(synthetic?900:values.size())){for(int j=0;j<6&&position<(synthetic?900:values.size());++j){double g=synthetic?.5+.1*sin(position/30.*2*M_PI*1.4):values[position];trace=core->step(g);history.push_back(g);++position;}if(position%90==0||position==(synthetic?900:values.size()))[self saveState];[self redraw];}}
-(void)saveState{lastSaveAttempt=NSDate.timeIntervalSinceReferenceDate;
#if TARGET_OS_IPHONE
 if(position==(synthetic?900:values.size()))UIApplication.sharedApplication.idleTimerDisabled=NO;
#endif
#if TARGET_OS_IPHONE
 NSString*dir=[NSSearchPathForDirectoriesInDomains(NSDocumentDirectory,NSUserDomainMask,YES)firstObject];
#else
 NSString*dir=[NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory,NSUserDomainMask,YES)firstObject];
#endif
 dir=[dir stringByAppendingPathComponent:@"HeartbeatNative"];NSError*error=nil;
 if(![[NSFileManager defaultManager]createDirectoryAtPath:dir withIntermediateDirectories:YES attributes:nil error:&error]){saveError=error.localizedDescription;outputSaved=NO;return;}
 NSDictionary*d=@{@"implementation":@"C++ translation of recovered Algorithm.mm with bounded native filter",@"input":synthetic?@"synthetic 84 bpm":@"BIDMC01 recorded PPG",@"frames":@(position),@"total_frames":@(synthetic?900:values.size()),@"bpm":trace.calibration_over?(id)@(trace.bpm_latest):(id)NSNull.null,@"calibrated":@(BOOL(trace.calibration_over)),@"complete":@(position==(synthetic?900:values.size())),@"source_hz":@30,@"nominal_replay_speed":@6};
 NSData*data=[NSJSONSerialization dataWithJSONObject:d options:NSJSONWritingPrettyPrinted error:&error];
 NSString*name=synthetic?@"synthetic84-state.json":@"bidmc01-state.json";
 outputSaved=data&&[data writeToFile:[dir stringByAppendingPathComponent:name] options:NSDataWritingAtomic error:&error]&&[data writeToFile:[dir stringByAppendingPathComponent:@"native-state.json"] options:NSDataWritingAtomic error:&error];if(outputSaved&&position==(synthetic?900:values.size())){
 NSString*completed=synthetic?@"synthetic84-complete.json":@"bidmc01-complete.json";
 outputSaved=[data writeToFile:[dir stringByAppendingPathComponent:completed] options:NSDataWritingAtomic error:&error];}
 saveError=outputSaved?nil:(error.localizedDescription?:@"Could not save native result");
#if TARGET_OS_IPHONE
 if(position==(synthetic?900:values.size()))UIApplication.sharedApplication.idleTimerDisabled=NO;
#endif
}
-(void)text:(NSString*)s x:(CGFloat)x y:(CGFloat)y size:(CGFloat)size color:(Color*)c width:(CGFloat)w{[s drawInRect:CGRectMake(x,y,w,100) withAttributes:@{NSFontAttributeName:[Font systemFontOfSize:size],NSForegroundColorAttributeName:c}];}
-(void)drawRect:(CGRect)dirty{
#if TARGET_OS_IPHONE
 CGContextRef c=UIGraphicsGetCurrentContext();CGFloat top=self.safeAreaInsets.top+16;
#else
 CGContextRef c=NSGraphicsContext.currentContext.CGContext;CGFloat top=26;
#endif
 CGFloat w=self.bounds.size.width,h=self.bounds.size.height;CGContextSetRGBFillColor(c,.035,.055,.09,1);CGContextFillRect(c,self.bounds);Color*white=[Color colorWithWhite:.95 alpha:1],*muted=[Color colorWithWhite:.68 alpha:1],*cyan=[Color colorWithRed:.2 green:.85 blue:.8 alpha:1];
 [self text:@"HeartBeat / native replay" x:22 y:top size:24 color:white width:w-44];
#if TARGET_OS_IPHONE
 NSString*platform=@"iOS · computed on this iPhone";
#else
 NSString*platform=@"macOS · native C++ processing";
#endif
 [self text:platform x:22 y:top+39 size:14 color:cyan width:w-44];[self text:synthetic?@"Synthetic waveform · known rate 84 bpm":@"BIDMC01 · recorded pulse-oximeter signal" x:22 y:top+69 size:16 color:white width:w-44];[self text:@"30 Hz input · nominal 6× replay · no camera input" x:22 y:top+96 size:14 color:muted width:w-44];
 NSString*bpm=trace.calibration_over?[NSString stringWithFormat:@"%.1f",trace.bpm_latest]:@"—";[self text:bpm x:22 y:top+143 size:62 color:cyan width:w-44];[self text:@"beats / minute · recovered estimator" x:24 y:top+220 size:14 color:muted width:w-44];
 CGRect graph=CGRectMake(22,top+269,w-44,MAX(100,MIN(210,h-top-420)));CGContextSetRGBFillColor(c,.07,.1,.15,1);CGContextFillRect(c,graph);CGContextSetRGBStrokeColor(c,.15,.23,.3,1);CGContextSetLineWidth(c,1);for(int j=1;j<4;++j){CGFloat y=graph.origin.y+j*graph.size.height/4;CGContextMoveToPoint(c,graph.origin.x,y);CGContextAddLineToPoint(c,CGRectGetMaxX(graph),y);}CGContextStrokePath(c);
 size_t begin=history.size()>240?history.size()-240:0;double lo=1,hi=0;for(size_t i=begin;i<history.size();++i){lo=std::min(lo,history[i]);hi=std::max(hi,history[i]);}if(hi-lo<1e-8){lo-=.1;hi+=.1;}CGContextSetRGBStrokeColor(c,.2,.85,.8,1);CGContextSetLineWidth(c,2);for(size_t i=begin;i<history.size();++i){CGFloat x=graph.origin.x+(i-begin)/239.*graph.size.width,y=CGRectGetMaxY(graph)-12-(history[i]-lo)/(hi-lo)*(graph.size.height-24);if(i==begin)CGContextMoveToPoint(c,x,y);else CGContextAddLineToPoint(c,x,y);}CGContextStrokePath(c);
 CGFloat bottom=CGRectGetMaxY(graph)+16;[self text:[NSString stringWithFormat:@"Frame %lu / %lu   ·   %.1f s of input",(unsigned long)position,(unsigned long)(synthetic?900:values.size()),position/30.] x:22 y:bottom size:14 color:white width:w-44];[self text:saveError?[@"Output/input error: " stringByAppendingString:saveError]:paused?@"Paused":position==(synthetic?900:values.size())?(outputSaved?@"Complete · results saved":@"Complete · output not saved"):trace.calibration_over?@"Estimating · legacy smoothing retained":@"Calibrating from observed input" x:22 y:bottom+25 size:14 color:cyan width:w-44];
 for(int i=0;i<3;++i){
#if TARGET_OS_IPHONE
 UIView*b=[self viewWithTag:100+i];
#else
 NSView*b=[self viewWithTag:100+i];
#endif
 b.frame=CGRectMake(22+i*(w-34)/3,bottom+64,(w-58)/3,42);
 }
 [self text:@"Updated replay interface; original authors: Or Maayan and Michael Leybovich. Research prototype; not a clinical measurement. Bundled PPG: BIDMC / PhysioNet 1.0.0 · ODC-By 1.0." x:22 y:bottom+125 size:12 color:muted width:w-44];
}
@end
#if TARGET_OS_IPHONE
@interface AppDelegate:UIResponder<UIApplicationDelegate>
@property(nonatomic,strong)UIWindow*window;
@end
@implementation AppDelegate
-(BOOL)application:(UIApplication*)app didFinishLaunchingWithOptions:(NSDictionary*)opts{self.window=[[UIWindow alloc]initWithFrame:UIScreen.mainScreen.bounds];UIViewController*v=[UIViewController new];v.view=[[HBView alloc]initWithFrame:self.window.bounds];self.window.rootViewController=v;[self.window makeKeyAndVisible];app.idleTimerDisabled=YES;return YES;}
@end
int main(int argc,char**argv){@autoreleasepool{return UIApplicationMain(argc,argv,nil,NSStringFromClass(AppDelegate.class));}}
#else
@interface AppDelegate:NSObject<NSApplicationDelegate>
@property(strong)NSWindow*window;
@end
@implementation AppDelegate
-(void)applicationDidFinishLaunching:(NSNotification*)n{self.window=[[NSWindow alloc]initWithContentRect:NSMakeRect(0,0,650,770) styleMask:NSWindowStyleMaskTitled|NSWindowStyleMaskClosable|NSWindowStyleMaskMiniaturizable backing:NSBackingStoreBuffered defer:NO];self.window.title=@"HeartBeat — updated native replay";self.window.contentView=[[HBView alloc]initWithFrame:NSMakeRect(0,0,650,770)];[self.window center];[self.window makeKeyAndOrderFront:nil];[NSApp activateIgnoringOtherApps:YES];}
-(BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication*)s{return YES;}
@end
int main(){@autoreleasepool{NSApplication*a=NSApplication.sharedApplication;[a setActivationPolicy:NSApplicationActivationPolicyRegular];AppDelegate*d=[AppDelegate new];a.delegate=d;[a run];}}
#endif
