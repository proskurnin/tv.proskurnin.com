import Foundation
import CoreGraphics
import CoreText
import ImageIO
let out=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
for p in ["intro","loop"] {try FileManager.default.createDirectory(at:out.appendingPathComponent(p),withIntermediateDirectories:true)}
let cs=CGColorSpaceCreateDeviceRGB()
func col(_ r:CGFloat,_ g:CGFloat,_ b:CGFloat,_ a:CGFloat=1)->CGColor {CGColor(colorSpace:cs,components:[r,g,b,a])!}
func render(_ progress:CGFloat)->CGImage {
 let c=CGContext(data:nil,width:1920,height:1080,bitsPerComponent:8,bytesPerRow:1920*4,space:cs,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
 c.setFillColor(col(0.007,0.012,0.03));c.fill(CGRect(x:0,y:0,width:1920,height:1080))
 let palette=[col(0.02,0.5,1),col(0.15,0.9,0.85),col(0.42,0.2,1),col(0.95,0.1,0.55)]
 let grad=CGGradient(colorsSpace:cs,colors:palette as CFArray,locations:[0,0.35,0.7,1])!
 for (x,y,r,g,b) in [(CGFloat(250),CGFloat(280),CGFloat(0.05),CGFloat(0.3),CGFloat(0.85)),(CGFloat(1680),CGFloat(820),CGFloat(0.55),CGFloat(0.05),CGFloat(0.5))] {
 let glow=CGGradient(colorsSpace:cs,colors:[col(r,g,b,0.3),col(r,g,b,0)] as CFArray,locations:[0,1])!
 c.drawRadialGradient(glow,startCenter:CGPoint(x:x,y:y),startRadius:0,endCenter:CGPoint(x:x,y:y),endRadius:880,options:[])
 }
 for j in 0..<22 {
 let k=CGFloat(j);let p=CGMutablePath();let a=sin(progress*CGFloat.pi)*90
 p.move(to:CGPoint(x:-180,y:90+k*12));p.addCurve(to:CGPoint(x:2110,y:1040-k*10),control1:CGPoint(x:580,y:850+k*9+a),control2:CGPoint(x:1190,y:80+k*5-a))
 c.saveGState();c.addPath(p.copy(strokingWithWidth:1.4,lineCap:.round,lineJoin:.round,miterLimit:1));c.clip();c.setAlpha(0.13+0.14*sin(k/22*CGFloat.pi));c.drawLinearGradient(grad,start:CGPoint(x:0,y:0),end:CGPoint(x:1920,y:1080),options:[]);c.restoreGState()
 }
 let fade=min(1,progress*2.5); let font=CTFontCreateWithName("HelveticaNeue-Medium" as CFString,158,nil)
 let s=NSAttributedString(string:"Proskurnin",attributes:[NSAttributedString.Key(kCTFontAttributeName as String):font,NSAttributedString.Key(kCTForegroundColorFromContextAttributeName as String):true,NSAttributedString.Key(kCTKernAttributeName as String):2])
 let line=CTLineCreateWithAttributedString(s);let bounds=CTLineGetBoundsWithOptions(line,[.useGlyphPathBounds]);let full=bounds.width+220;let left=(1920-full)/2
 c.saveGState();c.setAlpha(fade);c.setShadow(offset:CGSize(width:0,height:4),blur:28,color:col(0,0,0,0.8));c.setFillColor(col(0.96,0.98,1));c.textPosition=CGPoint(x:left-bounds.minX,y:540-bounds.midY-18*(1-fade));CTLineDraw(line,c);c.restoreGState()
 let pill=CGRect(x:left+bounds.width+45,y:474,width:175,height:132)
 c.saveGState();c.setAlpha(fade);c.addPath(CGPath(roundedRect:pill,cornerWidth:29,cornerHeight:29,transform:nil));c.clip();c.drawLinearGradient(grad,start:CGPoint(x:pill.minX,y:pill.minY),end:CGPoint(x:pill.maxX,y:pill.maxY),options:[]);c.restoreGState()
 let tv=CTLineCreateWithAttributedString(NSAttributedString(string:"TV",attributes:[NSAttributedString.Key(kCTFontAttributeName as String):CTFontCreateWithName("HelveticaNeue-Bold" as CFString,80,nil),NSAttributedString.Key(kCTForegroundColorFromContextAttributeName as String):true]));let tb=CTLineGetBoundsWithOptions(tv,[.useGlyphPathBounds]);c.setAlpha(fade);c.setFillColor(col(1,1,1));c.textPosition=CGPoint(x:pill.midX-tb.midX,y:pill.midY-tb.midY);CTLineDraw(tv,c)
 return c.makeImage()!
}
func save(_ im:CGImage,_ path:String,_ type:String,_ quality:Double=0.7){let d=CGImageDestinationCreateWithURL(out.appendingPathComponent(path) as CFURL,type as CFString,1,nil)!;CGImageDestinationAddImage(d,im,[kCGImageDestinationLossyCompressionQuality:quality] as CFDictionary);precondition(CGImageDestinationFinalize(d))}
for i in 0..<20 {save(render(CGFloat(i)/19),String(format:"intro/%03d.jpg",i),"public.jpeg")}
save(render(1),"loop/000.jpg","public.jpeg");save(render(1),"preview.png","public.png");save(render(1),"bootlogo.jpg","public.jpeg",0.2)
print("Full HD 1920x1080; 20 intro frames + static hold")
