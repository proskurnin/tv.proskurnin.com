import Foundation
import CoreGraphics
import CoreText
import ImageIO
let out=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
for p in ["intro","loop"] {try FileManager.default.createDirectory(at:out.appendingPathComponent(p),withIntermediateDirectories:true)}
let cs=CGColorSpaceCreateDeviceRGB()
func render(_ opacity:CGFloat)->CGImage {
 let c=CGContext(data:nil,width:1920,height:1080,bitsPerComponent:8,bytesPerRow:7680,space:cs,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
 c.setFillColor(CGColor(gray:0,alpha:1));c.fill(CGRect(x:0,y:0,width:1920,height:1080))
 let font=CTFontCreateWithName("HelveticaNeue-Medium" as CFString,126,nil)
 let line=CTLineCreateWithAttributedString(NSAttributedString(string:"Proskurnin TV",attributes:[NSAttributedString.Key(kCTFontAttributeName as String):font,NSAttributedString.Key(kCTForegroundColorFromContextAttributeName as String):true]))
 let b=CTLineGetBoundsWithOptions(line,[.useGlyphPathBounds]);c.setFillColor(CGColor(gray:opacity,alpha:1));c.textPosition=CGPoint(x:960-b.midX,y:540-b.midY);CTLineDraw(line,c);return c.makeImage()!
}
func save(_ im:CGImage,_ name:String,_ type:String){let d=CGImageDestinationCreateWithURL(out.appendingPathComponent(name) as CFURL,type as CFString,1,nil)!;CGImageDestinationAddImage(d,im,[kCGImageDestinationLossyCompressionQuality:0.45] as CFDictionary);precondition(CGImageDestinationFinalize(d))}
for i in 0..<8 {save(render(CGFloat(i)/7),String(format:"intro/%03d.png",i),"public.png")}
save(render(1),"loop/000.png","public.png");save(render(1),"preview.png","public.png");save(render(1),"bootlogo.jpg","public.jpeg")
