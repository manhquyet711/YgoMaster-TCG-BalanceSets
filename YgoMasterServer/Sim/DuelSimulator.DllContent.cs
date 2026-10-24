using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Runtime.InteropServices;
using System.IO;

namespace YgoMaster
{
    partial class DuelSimulator
    {
        public bool InitContent()
        {
            string cardDataDir = Path.Combine(DataDir, "CardData");
            if (!Directory.Exists(cardDataDir))
            {
                return false;
            }

            byte[] bufferInternalID = File.ReadAllBytes(Path.Combine(cardDataDir, "#", "CARD_IntID.bytes"));
            DLL_SetInternalID(Pin(bufferInternalID));

            byte[] bufferProp = File.ReadAllBytes(Path.Combine(cardDataDir, "#", "CARD_Prop.bytes"));
            DLL_SetCardProperty(Pin(bufferProp), bufferProp.Length);

            byte[] bufferSame = File.ReadAllBytes(Path.Combine(cardDataDir, "MD", "CARD_Same.bytes"));
            DLL_SetCardSame(Pin(bufferSame), bufferSame.Length);
            
            byte[] bufferGenre = File.ReadAllBytes(Path.Combine(cardDataDir, "#", "CARD_Genre.bytes"));
            DLL_SetCardGenre(Pin(bufferGenre));
            
            byte[] bufferNamed = File.ReadAllBytes(Path.Combine(cardDataDir, "#", "CARD_Named.bytes"));
            DLL_SetCardNamed(Pin(bufferNamed));
            
            byte[] bufferLink = File.ReadAllBytes(Path.Combine(cardDataDir, "MD", "CARD_Link.bytes"));
            DLL_SetCardLink(Pin(bufferLink), bufferLink.Length);

            return true;
        }

        // duel.dll keeps pointers to the card tables, so they must stay at a fixed address for
        // the whole process (like Pvp.GetPtr). Passing byte[] directly let them move or be freed,
        // which crashed DLL_DuelSysClearWork with an access violation.
        static IntPtr Pin(byte[] buffer)
        {
            IntPtr res = Marshal.AllocHGlobal(buffer.Length);
            Marshal.Copy(buffer, 0, res, buffer.Length);
            return res;
        }

        [DllImport(dllName)]
        private static extern int DLL_CardCheckName(int cardId, int nameType);
        [DllImport(dllName)]
        private static extern int DLL_CardGetAltCardID(int cardId, int alterID);
        [DllImport(dllName)]
        private static extern int DLL_CardGetAlterID(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetAtk(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetAtk2(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetAttr(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetBasicVal(int cardId, ref BasicVal pVal);
        [DllImport(dllName)]
        private static extern int DLL_CardGetDef(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetDef2(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetFrame(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetIcon(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetInternalID(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetKind(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetLevel(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetLimitation(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetLinkCards(int cardId, IntPtr pLinkID);
        [DllImport(dllName)]
        private static extern int DLL_CardGetLinkMask(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetLinkNum(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetOriginalID(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetOriginalID2(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetRank(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetScaleL(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetScaleR(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetStar(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardGetType(int cardId);
        [DllImport(dllName)]
        private static extern int DLL_CardIsThisCardGenre(int cardId, int genreId);
        [DllImport(dllName)]
        private static extern int DLL_CardIsThisSameCard(int cardA, int cardB);
        [DllImport(dllName)]
        private static extern int DLL_CardIsThisTunerMonster(int cardId);
        [DllImport(dllName)]
        private static extern void DLL_SetCardGenre(IntPtr data);
        [DllImport(dllName)]
        private static extern void DLL_SetCardLink(IntPtr data, int size);
        [DllImport(dllName)]
        private static extern void DLL_SetCardNamed(IntPtr data);
        [DllImport(dllName)]
        private static extern int DLL_SetCardProperty(IntPtr data, int size);
        [DllImport(dllName)]
        private static extern void DLL_SetCardSame(IntPtr data, int size);
        [DllImport(dllName)]
        private static extern void DLL_SetInternalID(IntPtr data);
    }
}
